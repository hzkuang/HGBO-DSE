from torch_geometric.loader import DataLoader
from dataset_utils import *
import torch
import torch.nn.functional as F
from torch_geometric.nn.conv import SAGEConv, GCNConv, GATConv
from torch_geometric.nn.dense import Linear
from torch_geometric.nn.models import JumpingKnowledge
from torch_geometric.nn.pool import global_add_pool, global_max_pool, SAGPooling


target = ['lut', 'ff', 'dsp', 'bram', 'uram', 'srl', 'cp', 'power']
tar_idx = 1
jknFlag = 0


class HierNet(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, num_layers, conv_type, hls_dim, drop_out=0.0, pool_ratio=0.5):
        super(HierNet, self).__init__()

        self.drop_out = drop_out
        self.pool_ratio = pool_ratio
        if conv_type == 'gcn':
            conv = GCNConv
        elif conv_type == 'gat':
            conv = GATConv
        elif conv_type == 'sage':
            conv = SAGEConv
        else:
            conv = GCNConv

        self.convs = torch.nn.ModuleList()
        self.pools = torch.nn.ModuleList()

        for i in range(num_layers):
            if i == 0:
                self.convs.append(conv(in_channels, hidden_channels))
            else:
                self.convs.append(conv(hidden_channels, hidden_channels))
            self.pools.append(SAGPooling(hidden_channels, self.pool_ratio))
        if jknFlag:
            self.jkn = JumpingKnowledge('lstm', channels=hidden_channels, num_layers=2)

        self.global_pool = global_add_pool
        self.channels = [hidden_channels * 2 + hls_dim, 64, 64, 1]
        self.mlps = torch.nn.ModuleList()

        for i in range(len(self.channels) - 1):
            fc = Linear(self.channels[i], self.channels[i + 1])
            self.mlps.append(fc)

    def forward(self, x, edge_index, batch, hls_attr):

        x = x.to(torch.float32)
        h_list = []

        for step in range(len(self.convs)):
            x = self.convs[step](x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.drop_out, training=self.training)
            x, edge_index, _, batch, _, _ = self.pools[step](x, edge_index, None, batch, None)
            h = torch.cat([global_max_pool(x, batch), global_add_pool(x, batch)], dim=1)
            h_list.append(h)

        if jknFlag:
            x = self.jkn(h_list)
        x = h_list[0] + h_list[1] + h_list[2]
        x = torch.cat([x, hls_attr], dim=-1)

        for f in range(len(self.mlps)):
            if f < len(self.mlps) - 1:
                x = F.relu(self.mlps[f](x))
                x = F.dropout(x, p=self.drop_out, training=self.training)
            else:
                x = self.mlps[f](x)

        return x


def train(model, train_loader):
    model.train()
    total_mse = 0
    total_mape = 0
    for _, data in enumerate(train_loader):
        data = data.to(device)
        optimizer.zero_grad()
        hls_attr = data['hls_attr']
        out = model(data.x, data.edge_index, data.batch, hls_attr)
        out = out.view(-1)
        true_y = data['y'].t()
        mse = F.huber_loss(out, true_y[tar_idx]).float()
        mape = mape_loss(out, true_y[tar_idx]).float()
        loss = mse
        loss.backward()
        optimizer.step()
        total_mse += mse.item() * data.num_graphs
        total_mape += mape.item() * data.num_graphs
    ds = train_loader.dataset
    total_mse = total_mse / len(ds)
    total_mape = total_mape / len(ds)

    return total_mse, total_mape


def test(model, loader, epoch):
    model.eval()
    with torch.no_grad():
        mse = 0
        mape = 0
        y = []
        y_hat = []
        residual = []
        for _, data in enumerate(loader):
            data = data.to(device)
            hls_attr = data['hls_attr']
            out = model(data.x, data.edge_index, data.batch, hls_attr)
            out = out.view(-1)
            true_y = data['y'].t()
            mse += F.huber_loss(out, true_y[tar_idx]).float().item() * data.num_graphs  # MSE
            mape += mape_loss(out, true_y[tar_idx]).float().item() * data.num_graphs  # MAPE
            y.extend(true_y[tar_idx].cpu().numpy().tolist())
            y_hat.extend(out.cpu().detach().numpy().tolist())
            residual.extend((true_y[tar_idx] - out).cpu().detach().numpy().tolist())
        if epoch % 10 == 0:
            print('pred.y:', out)
            print('data.y:', true_y[tar_idx])
        ds = loader.dataset
        mse = mse / len(ds)
        mape = mape / len(ds)
    return mse, mape


if __name__ == "__main__":
    batch_size = 32
    dataset_dir = os.path.abspath('../dataset/std')
    model_dir = os.path.abspath('./model')
    dataset = os.listdir(dataset_dir)
    dataset_list = generate_dataset(dataset_dir, dataset, print_info=False)
    train_ds, test_ds = split_dataset(dataset_list, shuffle=True, seed=128)
    print('train_ds size = {}, test_ds size = {}'.format(len(train_ds), len(test_ds)))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=True, drop_last=True)

    data_ini = None
    for step, data in enumerate(train_loader):
        if step == 0:
            data_ini = data
            break

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = HierNet(in_channels=data_ini.num_features, hidden_channels=64, num_layers=3, conv_type='sage',
                    hls_dim=6, drop_out=0.0)
    model = model.to(device)
    print(model)

    LR = 0.005
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=0.001)
    # scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.9, last_epoch=-1)

    min_train_mape = 1
    min_test_mape = 1
    for epoch in range(500):
        train_loss, train_mape = train(model, train_loader)
        test_loss, test_mape = test(model, test_loader, epoch)
        print(f'Epoch: {epoch:03d}, Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}')
        print(f'Epoch: {epoch:03d}, Train MAPE: {train_mape:.4f}, Test MAPE: {test_mape:.4f}')

        if epoch % 10 == 0:
            # scheduler.step()
            for p in optimizer.param_groups:
                p['lr'] *= 0.9

        save_train = False
        if train_mape < min_train_mape:
            min_train_mape = train_mape
            save_train = True

        save_test = False
        if test_mape < min_test_mape:
            min_test_mape = test_mape
            save_test = True

        checkpoint_1 = {
            'model': model.state_dict(),
            'optimizer': optimizer.state_dict(),
            'epoch': epoch,
            'min_train_mape': min_train_mape
        }

        checkpoint_2 = {
            'model': model.state_dict(),
            'optimizer': optimizer.state_dict(),
            'epoch': epoch,
            'min_test_mape': min_test_mape
        }

        if save_train:
            torch.save(checkpoint_1, os.path.join(model_dir, target[tar_idx] + '_h64_d0_checkpoint_train.pt'))

        if save_test:
            torch.save(checkpoint_2, os.path.join(model_dir, target[tar_idx] + '_h64_d0_checkpoint_test.pt'))

    print('Min Train MAPE: ' + str(min_train_mape))
    print('Min Test MAPE: ' + str(min_test_mape))
