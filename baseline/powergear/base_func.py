import random
import numpy as np
import os
import torch
from torch import Tensor
from torch_sparse import masked_select_nnz


def mape_loss(output, target):
    return torch.mean(torch.abs((target - output) / target))


def list_of_groups(list_info, per_list_len):
    list_of_group = zip(*(iter(list_info),) * per_list_len)
    end_list = [list(i) for i in list_of_group]  # i is a tuple
    count = len(list_info) % per_list_len
    end_list.append(list_info[-count:]) if count != 0 else end_list
    return end_list


def split_dataset(all_list, shuffle=False, seed=None):
    first_10_y = []
    for i in all_list[0:10]:
        first_10_y.append(i.y)
    print("first ten train graphs Y before shuffle:", first_10_y)

    if shuffle and seed is not None:
        # random.shuffle(all_list)
        np.random.RandomState(seed=seed).shuffle(all_list)
        print("seed number:", seed)
    elif shuffle and seed is None:
        random.shuffle(all_list)
        print("seed number:", seed)

    first_10_y = []
    for i in all_list[0:10]:
        first_10_y.append(i.y)
    print("first ten train graphs Y after shuffle:", first_10_y)

    gamma = round(len(all_list) * 0.8)
    train = all_list[0:gamma]
    test = all_list[gamma:]
    return train, test


def generate_dataset(dataset_dir, dataset_name_list, print_info=False):
    dataset_list = list()
    for i in range(0, len(dataset_name_list)):
        path = os.path.join(dataset_dir, dataset_name_list[i])
        if os.path.isfile(path):
            tem_data = torch.load(path)
            dataset_list = dataset_list + tem_data
            if print_info:
                print(path)
    return dataset_list


def label_norm(dataset_list):
    y_list = list()
    for data in dataset_list:
        y_list.append(data.y)
    mean = np.mean(y_list)
    std = np.std(y_list)
    for data in dataset_list:
        data.y = float((data.y - mean) / std)
    return mean, std


def lase_direction_enhance(data, enhance=False, edge_attr_set=True, nodes_attr_set=True, relation=4, onevone=False,
                           search_lsit=None, test=True):
    print("edge_attr_set:", edge_attr_set)
    print("nodes_attr_set:", nodes_attr_set)
    print("relation:", relation)
    print("onevone:", onevone)
    for i in data:
        if relation == 8:
            i.edge_index = torch.cat([torch.cat([i.edge_index[0, :], i.edge_index[1, :]], dim=-1),
                                      torch.cat([i.edge_index[1, :], i.edge_index[0, :]], dim=-1)]).view([2, -1])
            i.edge_type = torch.cat([i.edge_type, (i.edge_type + 4)])
            i.edge_attr = torch.cat([i.edge_attr, i.edge_attr])
            if (not edge_attr_set) and (not nodes_attr_set):
                i.edge_attr = torch.zeros(i.edge_attr.shape)
                i.x = torch.zeros(i.x.shape)
            elif edge_attr_set and (not nodes_attr_set):
                i.x = torch.zeros(i.x.shape)
            elif (not edge_attr_set) and nodes_attr_set:
                i.edge_attr = torch.zeros(i.edge_attr.shape)
            else:
                pass
        elif relation == 1:
            i.edge_type = torch.zeros(i.edge_type.shape)
        else:
            if (not edge_attr_set) and (not nodes_attr_set):
                i.edge_attr = torch.zeros(i.edge_attr.shape)
                i.x = torch.zeros(i.x.shape)
            elif edge_attr_set and (not nodes_attr_set):
                i.x = torch.zeros(i.x.shape)
            elif (not edge_attr_set) and nodes_attr_set:
                i.edge_attr = torch.zeros(i.edge_attr.shape)
            else:
                pass
        if search_lsit is not None:
            for key, val in search_lsit.items():
                i.edge_type[i.edge_type == key] = val
            edge_list_2 = torch.cat([edge_list_2, i.edge_type])
        if onevone:
            i.overall = torch.cat((i.overall[0:1], i.overall[4:(len(i.overall))]))
        # i.edge_attr = torch.cat([i.edge_attr[:,0].view(-1,1),i.edge_attr[:,2].view(-1,1)],dim=-1)
        i.x = torch.cat([i.x[:, 0:4], i.x[:, 22:]], dim=-1)

    if enhance:
        large_data = [i for i in data if i.y >= 1000]
        large_data = [val for val in large_data for i in range(10)]
        data.extend(large_data)
    if test:
        new_data = [i for i in data if i.y >= 0]
    data = new_data

    return data


def masked_edge_index(edge_index, edge_mask):
    if isinstance(edge_index, Tensor):
        return edge_index[:, edge_mask]
    else:
        return masked_select_nnz(edge_index, edge_mask, layout='coo')


def masked_edge_attr(edge_attr, edge_mask):
    if isinstance(edge_attr, Tensor):
        return edge_attr[edge_mask, :]
    else:
        return masked_select_nnz(edge_attr, edge_mask, layout='coo')


def get_mean_and_std_overall(dataset_list):
    dataset_len = len(dataset_list)
    overall_attr = torch.Tensor([])
    for i in dataset_list:
        i.overall = torch.Tensor(i.overall)
        overall_attr = torch.cat([overall_attr, i.overall])

    overall_attr = overall_attr.view(dataset_len, -1)
    overall_mean = overall_attr.mean(dim=0)
    overall_std = overall_attr.std(dim=0)

    return overall_mean, overall_std


def norm_overall(dataset_list, mean_set, std_set):
    length = len(mean_set)
    for single_graph in dataset_list:
        for j in range(length):
            single_graph.overall[j] = (single_graph.overall[j] - mean_set[j]) / std_set[j]
        if type(single_graph.overall) == list:
            single_graph.overall = torch.stack(single_graph.overall)
        elif type(single_graph.overall) != torch.Tensor:
            print('type(single_graph.overall) != torch.Tensor or list: kernel_name = {}, prj_name = {}'.format(
                single_graph.kernel_name,
                single_graph.prj_name))
    return dataset_list
