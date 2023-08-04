import os
import pandas as pd
import numpy as np
from pareto_nd import *
from util import multiplyList


# Constant
WLUT: float = 0.3
WFF: float = 0.25
WDSP: float = 0.3
WBRAM: float = 0.05


wght = [WLUT, WFF, WDSP, WBRAM]
noLatList = ['bfs_bulk', 'fft_strided', 'nw', 'stencil3d']
nameList = ['aes', 'bfs_bulk', 'fft_strided', 'gemm_ncubed', 'md_knn', 'nw', 'sort_radix', 'spmv_ellpack',
            'stencil3d', 'viterbi']
folderList = ['aes/aes', 'bfs/bulk', 'fft/strided', 'gemm/ncubed', 'md/knn', 'nw/nw', 'sort/radix', 'spmv/ellpack',
              'stencil/stencil3d', 'viterbi/viterbi']

powerList = [0.361, 0.249, 0.301, 0.308, 1.516, 0.258, 0.253, 0.314, 0.278, 0.426]
latList = [713, 1000, 1000, 131369, 2467, 33664, 166289, 2529, 52821, 294737]
cpList = [7.742, 3.804, 9.064, 7.788, 9.716, 4.763, 4.189, 7.631, 6.187, 9.122]
areaList = [5144.1, 288.7, 1343.8, 4305.05, 22375.35, 445.8, 1313.15, 1716.25, 310.9, 13590.3]

index = 9
name = nameList[index]
bench = folderList[index]
power = powerList[index]
cp = cpList[index]
area = areaList[index]

tidy_data = './tidy_data'
csv_impl = os.path.join(tidy_data, name + '_impl.csv')
data_impl = pd.read_csv(csv_impl, sep=',')
inputPoints_impl = []

for idx in range(100):
    impl_pwr = data_impl['pwr'][idx] / power
    impl_cp = data_impl['cp'][idx] / cp
    impl_usg = [data_impl['lut'][idx], data_impl['ff'][idx], data_impl['dsp'][idx], data_impl['bram'][idx]]
    impl_area = sum(np.multiply(wght, impl_usg)) / area
    if name not in noLatList:
        lat = latList[index]
        impl_lat = data_impl['lat'][idx] / lat
        inputPoints_impl.append([impl_pwr, impl_lat, impl_cp, impl_area])
    else:
        inputPoints_impl.append([impl_pwr, impl_cp, impl_area])

paretoPoints_impl, dominatedPoints_impl = simple_cull(inputPoints_impl, dominates)

listPLCA_impl = []
plca_impl = 0
for p in paretoPoints_impl:
    print(p)
    value = multiplyList(p)
    plca_impl += value
    listPLCA_impl.append(value)
plca_sa = plca_impl / len(paretoPoints_impl)
min_plca_impl = min(listPLCA_impl)
print("MINIMUM IMPL PDA: " + str(round(min_plca_impl, 4)))
