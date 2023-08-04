import torch.nn.functional as F
from torch_geometric.nn.conv import GCNConv
from torch_geometric.nn.dense import Linear
from torch_geometric.nn.pool import global_mean_pool
from torch_geometric.loader import DataLoader
from dataset_utils import *


class GCNNet(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels=None, num_layers=2, drop_out=0.1):
        super(GCNNet, self).__init__()

        if hidden_channels is None:
            hidden_channels = [64, 128]
        self.drop_out = drop_out
        self.convs = torch.nn.ModuleList()

        for i in range(num_layers):
            if i == 0:
                self.convs.append(GCNConv(in_channels, hidden_channels[i]))
            else:
                self.convs.append(GCNConv(hidden_channels[i - 1], hidden_channels[i]))

        self.global_pool = global_mean_pool
        self.channels = [128, 64, 64, 64, 1]
        self.mlps = torch.nn.ModuleList()

        for i in range(len(self.channels) - 1):
            fc = Linear(self.channels[i], self.channels[i + 1])
            self.mlps.append(fc)

    def forward(self, x, edge_index, batch):

        x = x.to(torch.float32)

        for idx in range(len(self.convs)):
            x = self.convs[idx](x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=0.0, training=self.training)

        x = self.global_pool(x, batch)

        for f in range(len(self.mlps)):
            if f < len(self.mlps) - 1:
                if f == 0:
                    x = F.leaky_relu(self.mlps[f](x), negative_slope=0.2)
                else:
                    x = F.leaky_relu(self.mlps[f](x), negative_slope=0.1)
                x = F.dropout(x, p=self.drop_out, training=self.training)
            else:
                x = self.mlps[f](x)
                x = F.relu(x)

        return x


target = ['lut', 'ff', 'dsp', 'bram', 'uram', 'srl', 'cp', 'power']
tar_idx = 6


def train(model, train_loader):
    model.train()
    total_mse = 0
    total_mape = 0
    for _, data in enumerate(train_loader):
        data = data.to(device)
        optimizer.zero_grad()
        out = model(data.x, data.edge_index, data.batch)
        out = out.view(-1)
        true_y = data['y'].t()
        mse = msle_loss(out, true_y[tar_idx]).float()
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
            out = model(data.x, data.edge_index, data.batch)
            out = out.view(-1)
            true_y = data['y'].t()
            mse += msle_loss(out, true_y[tar_idx]).float().item() * data.num_graphs  # MSE
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
    dataset_dir = os.path.abspath('../../dataset/rdc')
    model_dir = './model'

    dataset = os.listdir(dataset_dir)
    dataset_list = generate_dataset(dataset_dir, dataset, print_info=False)
    train_ds, test_ds = split_dataset(dataset_list, shuffle=True, seed=128)
    print('train_ds size = {}, test_ds size = {}'.format(len(train_ds), len(test_ds)))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, drop_last=False)

    data_ini = None
    for step, data in enumerate(train_loader):
        if step == 0:
            data_ini = data
            break

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = GCNNet(in_channels=data_ini.num_features)
    model = model.to(device)
    print(model)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=0.001)
    scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.9, last_epoch=-1)

    min_train_mape = 1
    min_test_mape = 1
    for epoch in range(500):
        train_loss, train_mape = train(model, train_loader)
        test_loss, test_mape = test(model, test_loader, epoch)
        print(f'Epoch: {epoch:03d}, Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}')
        print(f'Epoch: {epoch:03d}, Train MAPE: {train_mape:.4f}, Test MAPE: {test_mape:.4f}')

        if epoch % 10 == 0:
            scheduler.step()

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
            torch.save(checkpoint_1, os.path.join(model_dir, target[tar_idx] + '_checkpoint_train.pt'))

        if save_test:
            torch.save(checkpoint_2, os.path.join(model_dir, target[tar_idx] + '_checkpoint_test.pt'))
