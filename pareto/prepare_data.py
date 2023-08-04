import os
import csv
import json
from util import getListPPA

noLatList = ['bfs_bulk', 'fft_strided', 'nw', 'stencil3d']

algList = ['sa.csv', 'nsga.csv', 'motpe_d.csv', 'motpe_f.csv', 'motpe_fl.csv']
nameList = ['aes', 'bfs_bulk', 'fft_strided', 'gemm_ncubed', 'md_knn', 'nw', 'sort_radix', 'spmv_ellpack',
            'stencil3d', 'viterbi']
folderList = ['aes/aes', 'bfs/bulk', 'fft/strided', 'gemm/ncubed', 'md/knn', 'nw/nw', 'sort/radix', 'spmv/ellpack',
              'stencil/stencil3d', 'viterbi/viterbi']

index = 9

name = nameList[index]
bench = folderList[index]

root = os.path.abspath('../dse_ds/MachSuite')

path_sa = os.path.join(root, 'sa_ds')
path_ga = os.path.join(root, 'nsga_ds')
path_d = os.path.join(root, 'motpe_d_ds')
path_f = os.path.join(root, 'motpe_f_ds')
path_fl = os.path.join(root, 'motpe_fl_ds')

tidy_data = './tidy_data'

path_sa = os.path.join(path_sa, bench, 'p1/script')
path_ga = os.path.join(path_ga, bench, 'p1/script')
path_d = os.path.join(path_d, bench, 'p1/script')
path_f = os.path.join(path_f, bench, 'p1/script')
path_fl = os.path.join(path_fl, bench, 'p1/script')

listPPA_sa = getListPPA(path_sa)
listPPA_ga = getListPPA(path_ga)
listPPA_d = getListPPA(path_d)
listPPA_f = getListPPA(path_f)
listPPA_fl = getListPPA(path_fl)

AllList = [listPPA_sa, listPPA_ga, listPPA_d, listPPA_f, listPPA_fl]

for idx in range(len(AllList)):
    listPPA = AllList[idx]
    pwr_list = []
    lat_list = []
    cp_list = []
    lut_list = []
    ff_list = []
    dsp_list = []
    bram_list = []

    for ppa_rpt in listPPA:
        f = open(ppa_rpt)
        data = json.load(f)

        pwr = data['IMPL']['PWR']
        cp = data['IMPL']['CP']
        lut = data['IMPL']['LUT']
        ff = data['IMPL']['FF']
        dsp = data['IMPL']['DSP']
        bram = data['IMPL']['BRAM']

        pwr_list.append(pwr)
        cp_list.append(cp)
        lut_list.append(lut)
        ff_list.append(ff)
        dsp_list.append(dsp)
        bram_list.append(bram)

        if name in noLatList:
            pass
        else:
            lat = data['LATENCY']['Latency']
            lat_list.append(lat)

    alg = algList[idx]
    csv_tb = os.path.join(tidy_data, name + '_' + alg)
    if name in noLatList:
        title = ['pwr', 'cp', 'lut', 'ff', 'dsp', 'bram']
    else:
        title = ['pwr', 'lat', 'cp', 'lut', 'ff', 'dsp', 'bram']
    with open(csv_tb, 'w', newline='') as wfile:
        writer = csv.writer(wfile)
        writer.writerow(title)
        if name in noLatList:
            for i in range(len(pwr_list)):
                wr_line = [pwr_list[i], cp_list[i],
                           lut_list[i], ff_list[i], dsp_list[i], bram_list[i]]
                writer.writerow(wr_line)
        else:
            for i in range(len(pwr_list)):
                wr_line = [pwr_list[i], lat_list[i], cp_list[i],
                           lut_list[i], ff_list[i], dsp_list[i], bram_list[i]]
                writer.writerow(wr_line)
