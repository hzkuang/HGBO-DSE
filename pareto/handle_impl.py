import os
import csv
import json
from util import getListPPA


noLatList = ['bfs_bulk', 'fft_strided', 'nw', 'stencil3d']
nameList = ['aes', 'bfs_bulk', 'fft_strided', 'gemm_ncubed', 'md_knn', 'nw', 'sort_radix', 'spmv_ellpack',
            'stencil3d', 'viterbi']
folderList = ['aes/aes', 'bfs/bulk', 'fft/strided', 'gemm/ncubed', 'md/knn', 'nw/nw', 'sort/radix', 'spmv/ellpack',
              'stencil/stencil3d', 'viterbi/viterbi']

index = 0
name = nameList[index]
bench = folderList[index]

path_impl = os.path.abspath('../dse_ds/MachSuite/impl_ds')
path_impl = os.path.join(path_impl, bench, 'p1/script')
listPPA_impl = getListPPA(path_impl)

tidy_data = './tidy_data'

pwr_list = []
lat_list = []
cp_list = []
lut_list = []
ff_list = []
dsp_list = []
bram_list = []

for ppa_rpt in listPPA_impl:
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

csv_tb = os.path.join(tidy_data, name + '_impl.csv')
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
