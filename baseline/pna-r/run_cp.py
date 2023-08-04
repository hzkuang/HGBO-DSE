from torch_geometric.loader import DataLoader
from torch_geometric.utils import degree
from dataset_utils import *
from pna import *


target = ['lut', 'ff', 'dsp', 'bram', 'uram', 'srl', 'cp', 'power']
tar_idx = 6


def train(model, train_loader):
    model.train()
    total_mse = 0
    total_mape = 0
    for _, data in enumerate(train_loader):
        # print('Batch: ' + str(_))
        data = data.to(device)
        optimizer.zero_grad()
        out = model(data)
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
            out = model(data)
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

    # compute the maximum in-degree in the training data.
    max_degree = -1
    for data in train_ds:
        d = degree(data.edge_index[1], num_nodes=data.num_nodes, dtype=torch.long)
        max_degree = max(max_degree, int(d.max()))

    # compute the in-degree histogram tensor
    deg = torch.zeros(max_degree + 1, dtype=torch.long)
    for data in train_ds:
        d = degree(data.edge_index[1], num_nodes=data.num_nodes, dtype=torch.long)
        deg += torch.bincount(d, minlength=deg.numel())

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = Net(in_dim=data_ini.num_features, deg=deg, num_tasks=1, num_layer=5, emb_dim=300, edge_dim=2,
                drop_ratio=0.5)
    model = model.to(device)
    print(model)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.8, patience=10,
                                                           min_lr=0.00001)

    min_train_mape = 1
    min_test_mape = 1
    for epoch in range(100):
        train_loss, train_mape = train(model, train_loader)
        test_loss, test_mape = test(model, test_loader, epoch)
        print(f'Epoch: {epoch:03d}, Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}')
        print(f'Epoch: {epoch:03d}, Train MAPE: {train_mape:.4f}, Test MAPE: {test_mape:.4f}')

        scheduler.step(metrics=train_loss)

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
