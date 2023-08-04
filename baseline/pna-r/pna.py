import torch
import torch.nn.functional as F
from torch.nn import ModuleList
from torch.nn import Sequential, ReLU, Linear
from torch_geometric.nn.conv import PNAConv
from torch_geometric.nn.pool import global_add_pool, global_mean_pool, global_max_pool
from torch_geometric.nn.aggr import AttentionalAggregation, Set2Set
from torch.nn import BatchNorm1d
# from torch_geometric.nn.norm import BatchNorm


class Net(torch.nn.Module):
    def __init__(self, in_dim, deg, num_tasks=1, num_layer=5, emb_dim=300, edge_dim=2, drop_ratio=0.5, JK="last",
                 residual=False, graph_pooling="sum"):
        super(Net, self).__init__()

        self.num_layer = num_layer
        self.drop_ratio = drop_ratio
        self.JK = JK

        self.residual = residual  # add residual connection or not
        self.emb_dim = emb_dim
        self.edge_dim = edge_dim
        self.num_tasks = num_tasks
        self.graph_pooling = graph_pooling
        self.deg = deg

        if self.num_layer < 2:
            raise ValueError("Number of GNN layers must be greater than 1.")

        aggregators = ['mean', 'min', 'max', 'std']
        scalers = ['identity', 'amplification', 'attenuation']

        self.convs = ModuleList()
        # self.batch_norms = ModuleList()
        for idx in range(num_layer):
            if idx == 0:
                conv = PNAConv(in_channels=in_dim, out_channels=emb_dim,
                               aggregators=aggregators, scalers=scalers, deg=deg,
                               edge_dim=edge_dim, towers=6, pre_layers=1, post_layers=1,
                               divide_input=False)
            else:
                conv = PNAConv(in_channels=emb_dim, out_channels=emb_dim,
                               aggregators=aggregators, scalers=scalers, deg=deg,
                               edge_dim=edge_dim, towers=6, pre_layers=1, post_layers=1,
                               divide_input=False)
            self.convs.append(conv)
            # self.batch_norms.append(BatchNorm(emb_dim))

        # pooling function to generate whole-graph embeddings
        if self.graph_pooling == "sum":
            self.pool = global_add_pool
        elif self.graph_pooling == "mean":
            self.pool = global_mean_pool
        elif self.graph_pooling == "max":
            self.pool = global_max_pool
        elif self.graph_pooling == "attention":
            self.pool = AttentionalAggregation(
                gate_nn=Sequential(Linear(emb_dim, 2 * emb_dim), BatchNorm1d(2 * emb_dim), ReLU(),
                                   Linear(2 * emb_dim, 1)))
        elif self.graph_pooling == "set2set":
            self.pool = Set2Set(emb_dim, processing_steps=2)
        else:
            raise ValueError("Invalid graph pooling type.")

        self.graph_pred_linear = ModuleList()
        # self.graph_norm = ModuleList()

        if graph_pooling == "set2set":
            self.graph_pred_linear.append(Linear(2 * emb_dim, 2 * emb_dim))
            self.graph_pred_linear.append(Linear(2 * emb_dim, emb_dim))
            self.graph_pred_linear.append(Linear(emb_dim, self.num_tasks))

            # self.graph_norm.append(BatchNorm(2 * emb_dim))
            # self.graph_norm.append(BatchNorm(emb_dim))
        else:
            self.graph_pred_linear.append(Linear(emb_dim, 2 * emb_dim))
            self.graph_pred_linear.append(Linear(2 * emb_dim, emb_dim))
            self.graph_pred_linear.append(Linear(emb_dim, self.num_tasks))

            # self.graph_norm.append(BatchNorm(2 * emb_dim))
            # self.graph_norm.append(BatchNorm(emb_dim))

    def forward(self, batched_data):
        x, edge_index, edge_attr, batch = batched_data.x, batched_data.edge_index, batched_data.edge_attr, \
            batched_data.batch

        h_list = [x.to(torch.float32)]

        for layer in range(self.num_layer):

            h = self.convs[layer](x=h_list[layer], edge_index=edge_index, edge_attr=edge_attr)
            # h = self.batch_norms[layer](h)

            if layer == self.num_layer - 1:
                # remove relu for the last layer
                h = F.dropout(h, self.drop_ratio, training=self.training)
            else:
                h = F.dropout(F.relu(h), self.drop_ratio, training=self.training)

            if self.residual:
                h += h_list[layer]

            h_list.append(h)

        # different implementations of JK-concat
        if self.JK == "last":
            node_representation = h_list[-1]
        elif self.JK == "sum":
            node_representation = 0
            for layer in range(self.num_layer):
                if layer > 0:
                    node_representation += h_list[layer]
        else:
            node_representation = h_list[-1]

        h_graph = self.pool(node_representation, batched_data.batch)

        # final prediction
        h_graph = self.graph_pred_linear[0](h_graph)
        # h_graph = self.graph_norm[0](h_graph)
        h_graph = F.dropout(F.relu(h_graph), self.drop_ratio, training=self.training)

        h_graph = self.graph_pred_linear[1](h_graph)
        # h_graph = self.graph_norm[1](h_graph)
        h_graph = F.dropout(F.relu(h_graph), self.drop_ratio, training=self.training)

        return F.relu(self.graph_pred_linear[2](h_graph))
