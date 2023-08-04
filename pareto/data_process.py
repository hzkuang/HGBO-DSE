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
algList = ['sa.csv', 'nsga.csv', 'motpe_d.csv', 'motpe_f.csv', 'motpe_fl.csv']

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

csv_sa = os.path.join(tidy_data, name + '_' + algList[0])
csv_nsga = os.path.join(tidy_data, name + '_' + algList[1])
csv_motpe_d = os.path.join(tidy_data, name + '_' + algList[2])
csv_motpe_f = os.path.join(tidy_data, name + '_' + algList[3])
csv_motpe_fl = os.path.join(tidy_data, name + '_' + algList[4])

data_sa = pd.read_csv(csv_sa, sep=',')
data_nsga = pd.read_csv(csv_nsga, sep=',')
data_motpe_d = pd.read_csv(csv_motpe_d, sep=',')
data_motpe_f = pd.read_csv(csv_motpe_f, sep=',')
data_motpe_fl = pd.read_csv(csv_motpe_fl, sep=',')

inputPoints = []
inputPoints_sa = []
inputPoints_nsga = []
inputPoints_motpe_d = []
inputPoints_motpe_f = []
inputPoints_motpe_fl = []

for idx in range(100):
    sa_pwr = data_sa['pwr'][idx] / power
    sa_cp = data_sa['cp'][idx] / cp
    sa_usg = [data_sa['lut'][idx], data_sa['ff'][idx], data_sa['dsp'][idx], data_sa['bram'][idx]]
    sa_area = sum(np.multiply(wght, sa_usg)) / area
    if name not in noLatList:
        lat = latList[index]
        sa_lat = data_sa['lat'][idx] / lat
        inputPoints_sa.append([sa_pwr, sa_lat, sa_cp, sa_area])
    else:
        inputPoints_sa.append([sa_pwr, sa_cp, sa_area])

    nsga_pwr = data_nsga['pwr'][idx] / power
    nsga_cp = data_nsga['cp'][idx] / cp
    nsga_usg = [data_nsga['lut'][idx], data_nsga['ff'][idx], data_nsga['dsp'][idx], data_nsga['bram'][idx]]
    nsga_area = sum(np.multiply(wght, nsga_usg)) / area
    if name not in noLatList:
        lat = latList[index]
        nsga_lat = data_nsga['lat'][idx] / lat
        inputPoints_nsga.append([nsga_pwr, nsga_lat, nsga_cp, nsga_area])
    else:
        inputPoints_nsga.append([nsga_pwr, nsga_cp, nsga_area])

    motpe_d_pwr = data_motpe_d['pwr'][idx] / power
    motpe_d_cp = data_motpe_d['cp'][idx] / cp
    motpe_d_usg = [data_motpe_d['lut'][idx], data_motpe_d['ff'][idx],
                   data_motpe_d['dsp'][idx], data_motpe_d['bram'][idx]]
    motpe_d_area = sum(np.multiply(wght, motpe_d_usg)) / area
    if name not in noLatList:
        lat = latList[index]
        motpe_d_lat = data_motpe_d['lat'][idx] / lat
        inputPoints_motpe_d.append([motpe_d_pwr, motpe_d_lat, motpe_d_cp, motpe_d_area])
    else:
        inputPoints_motpe_d.append([motpe_d_pwr, motpe_d_cp, motpe_d_area])

    motpe_f_pwr = data_motpe_f['pwr'][idx] / power
    motpe_f_cp = data_motpe_f['cp'][idx] / cp
    motpe_f_usg = [data_motpe_f['lut'][idx], data_motpe_f['ff'][idx],
                   data_motpe_f['dsp'][idx], data_motpe_f['bram'][idx]]
    motpe_f_area = sum(np.multiply(wght, motpe_f_usg)) / area
    if name not in noLatList:
        lat = latList[index]
        motpe_f_lat = data_motpe_f['lat'][idx] / lat
        inputPoints_motpe_f.append([motpe_f_pwr, motpe_f_lat, motpe_f_cp, motpe_f_area])
    else:
        inputPoints_motpe_f.append([motpe_f_pwr, motpe_f_cp, motpe_f_area])

    motpe_fl_pwr = data_motpe_fl['pwr'][idx] / power
    motpe_fl_cp = data_motpe_fl['cp'][idx] / cp
    motpe_fl_usg = [data_motpe_fl['lut'][idx], data_motpe_fl['ff'][idx],
                    data_motpe_fl['dsp'][idx], data_motpe_fl['bram'][idx]]
    motpe_fl_area = sum(np.multiply(wght, motpe_fl_usg)) / area
    if name not in noLatList:
        lat = latList[index]
        motpe_fl_lat = data_motpe_fl['lat'][idx] / lat
        inputPoints_motpe_fl.append([motpe_fl_pwr, motpe_fl_lat, motpe_fl_cp, motpe_fl_area])
    else:
        inputPoints_motpe_fl.append([motpe_fl_pwr, motpe_fl_cp, motpe_fl_area])

inputPoints.extend(inputPoints_sa)
inputPoints.extend(inputPoints_nsga)
inputPoints.extend(inputPoints_motpe_d)
inputPoints.extend(inputPoints_motpe_f)
inputPoints.extend(inputPoints_motpe_fl)

# reference front
paretoPoints, dominatedPoints = simple_cull(inputPoints, dominates)

paretoPoints_sa, dominatedPoints_sa = simple_cull(inputPoints_sa, dominates)
paretoPoints_nsga, dominatedPoints_nsga = simple_cull(inputPoints_nsga, dominates)
paretoPoints_motpe_d, dominatedPoints_motpe_d = simple_cull(inputPoints_motpe_d, dominates)
paretoPoints_motpe_f, dominatedPoints_motpe_f = simple_cull(inputPoints_motpe_f, dominates)
paretoPoints_motpe_fl, dominatedPoints_motpe_fl = simple_cull(inputPoints_motpe_fl, dominates)

print("Reference Set")
print("*" * 8 + " non-dominated answers " + ("*" * 8))
print('number: ' + str(len(paretoPoints)))
for p in paretoPoints:
    print(p)

print("SA Pareto Set")
print("*" * 8 + " non-dominated answers " + ("*" * 8))
print('number: ' + str(len(paretoPoints_sa)))
listPLCA_sa = []
plca_sa = 0
for p in paretoPoints_sa:
    print(p)
    value = multiplyList(p)
    plca_sa += value
    listPLCA_sa.append(value)
plca_sa = plca_sa / len(paretoPoints_sa)
min_plca_sa = min(listPLCA_sa)

print("NSGA Pareto Front")
print("*" * 8 + " non-dominated answers " + ("*" * 8))
print('number: ' + str(len(paretoPoints_nsga)))
listPLCA_nsga = []
plca_nsga = 0
for p in paretoPoints_nsga:
    print(p)
    value = multiplyList(p)
    plca_nsga += value
    listPLCA_nsga.append(value)
plca_nsga = plca_nsga / len(paretoPoints_nsga)
min_plca_nsga = min(listPLCA_nsga)

print("MOTPE_D Pareto Set")
print("*" * 8 + " non-dominated answers " + ("*" * 8))
print('number: ' + str(len(paretoPoints_motpe_d)))
listPLCA_motpe_d = []
plca_motpe_d = 0
for p in paretoPoints_motpe_d:
    print(p)
    value = multiplyList(p)
    plca_motpe_d += value
    listPLCA_motpe_d.append(value)
plca_motpe_d = plca_motpe_d / len(paretoPoints_motpe_d)
min_plca_motpe_d = min(listPLCA_motpe_d)

print("MOTPE_F Pareto Front")
print("*" * 8 + " non-dominated answers " + ("*" * 8))
print('number: ' + str(len(paretoPoints_motpe_f)))
listPLCA_motpe_f = []
plca_motpe_f = 0
for p in paretoPoints_motpe_f:
    print(p)
    value = multiplyList(p)
    plca_motpe_f += value
    listPLCA_motpe_f.append(value)
plca_motpe_f = plca_motpe_f/len(paretoPoints_motpe_f)
min_plca_motpe_f = min(listPLCA_motpe_f)

print("MOTPE_FL Pareto Front")
print("*" * 8 + " non-dominated answers " + ("*" * 8))
print('number: ' + str(len(paretoPoints_motpe_fl)))
listPLCA_motpe_fl = []
plca_motpe_fl = 0
for p in paretoPoints_motpe_fl:
    print(p)
    value = multiplyList(p)
    plca_motpe_fl += value
    listPLCA_motpe_fl.append(value)
plca_motpe_fl = plca_motpe_fl/len(paretoPoints_motpe_fl)
min_plca_motpe_fl = min(listPLCA_motpe_fl)

# PDA
print("MINIMUM SA PDA: " + str(round(min_plca_sa, 4)))
print("MINIMUM NSGA PDA: " + str(round(min_plca_nsga, 4)))
print("MINIMUM MOTPE_D PDA: " + str(round(min_plca_motpe_d, 4)))
print("MINIMUM MOTPE_F PDA: " + str(round(min_plca_motpe_f, 4)))
print("MINIMUM MOTPE_FL PDA: " + str(round(min_plca_motpe_fl, 4)))

# ADRS
diff = 0.0
for r in paretoPoints:
    dist = []
    for s in paretoPoints_sa:
        s = np.array(s)
        r = np.array(r)
        tmp = np.linalg.norm((s - r) / r, np.inf)
        dist.append(tmp)
    f = min(dist)
    diff += f
adrs_sa = diff / len(paretoPoints)
print("SA ADRS: " + str(round(adrs_sa, 4)))

diff = 0.0
for r in paretoPoints:
    dist = []
    for g in paretoPoints_nsga:
        g = np.array(g)
        r = np.array(r)
        tmp = np.linalg.norm((g - r) / r, np.inf)
        dist.append(tmp)
    f = min(dist)
    diff += f
adrs_nsga = diff / len(paretoPoints)
print("NSGA ADRS: " + str(round(adrs_nsga, 4)))

diff = 0.0
for r in paretoPoints:
    dist = []
    for d in paretoPoints_motpe_d:
        d = np.array(d)
        r = np.array(r)
        tmp = np.linalg.norm((d - r) / r, np.inf)
        dist.append(tmp)
    f = min(dist)
    diff += f
adrs_ds = diff / len(paretoPoints)
print("MOTPE_D ADRS: " + str(round(adrs_ds, 4)))

diff = 0.0
for r in paretoPoints:
    dist = []
    for b in paretoPoints_motpe_f:
        b = np.array(b)
        r = np.array(r)
        tmp = np.linalg.norm((b - r) / r, np.inf)
        dist.append(tmp)
    f = min(dist)
    diff += f
adrs_motpe_f = diff / len(paretoPoints)
print("MOTPE_F ADRS: " + str(round(adrs_motpe_f, 4)))

diff = 0.0
for r in paretoPoints:
    dist = []
    for motpe_fl in paretoPoints_motpe_fl:
        motpe_fl = np.array(motpe_fl)
        r = np.array(r)
        tmp = np.linalg.norm((motpe_fl - r) / r, np.inf)
        dist.append(tmp)
    f = min(dist)
    diff += f
adrs_motpe_fl = diff / len(paretoPoints)
print("MOTPE_FL ADRS: " + str(round(adrs_motpe_fl, 4)))
