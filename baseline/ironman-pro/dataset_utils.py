import os
import torch
import random
import numpy as np
from torch.utils.data import random_split


def mape_loss(output, target):
    return torch.mean(torch.abs((target - output) / target))


def msle_loss(output, target):
    output = torch.log(output + 1)
    target = torch.log(target + 1)
    return torch.mean(torch.square(output - target))


def generate_dataset(dataset_dir, dataset_name_list, print_info=False):
    dataset_list = list()
    for ds in dataset_name_list:
        ds_path = os.path.join(dataset_dir, ds)
        if os.path.isfile(ds_path):
            tem_data = torch.load(ds_path)
            dataset_list = dataset_list + tem_data
            if print_info:
                print(ds_path)
    return dataset_list


def split_dataset(all_list, shuffle=True, seed=6666):
    first_10_y = []
    for i in all_list[0:10]:
        first_10_y.append(i.y)
    print("first ten train graphs Y before shuffle:", first_10_y)

    if shuffle and seed is not None:
        np.random.RandomState(seed=seed).shuffle(all_list)
        print("seed number:", seed)
    elif shuffle and seed is None:
        random.shuffle(all_list)
        print("seed number:", seed)

    first_10_y = []
    for i in all_list[0:10]:
        first_10_y.append(i.y)
    print("first ten train graphs Y after shuffle:", first_10_y)

    train_ds, test_ds = random_split(all_list, [round(0.8 * len(all_list)), round(0.2 * len(all_list))],
                                     generator=torch.Generator().manual_seed(42))

    return train_ds, test_ds
