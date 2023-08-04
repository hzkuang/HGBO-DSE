import os
import numpy as np
from parse_xml import *


# Constant
F1: float = 1e8
F2: float = 1e8
F3: float = 1e8
F4: float = 1e8
WLUT: float = 0.3
WFF: float = 0.25
WDSP: float = 0.3
WBRAM: float = 0.05


def getHLS(params, rpt_list):

    fail_flag = False
    dictPPA = {}
    hls_rpt = rpt_list[0]
    hls_xml = rpt_list[1]

    LATENCY = F4
    dictLatency = {}
    if os.path.exists(hls_xml):
        print("[INFO] Reading Latency Information...")
        xml_parser = read_xml(hls_xml)
        root = get_xml_root(xml_parser)
        perf_info = find_first_node(root, 'PerformanceEstimates')
        latency_info = find_first_node(perf_info, 'SummaryOfOverallLatency')

        if latency_info.find('Best-caseLatency').text != 'undef':
            dictLatency['best_latency'] = int(latency_info.find('Best-caseLatency').text)
            dictLatency['worst_latency'] = int(latency_info.find('Worst-caseLatency').text)
            dictLatency['average_latency'] = int(latency_info.find('Average-caseLatency').text)
            dictLatency['best_time_latency'] = latency_info.find('Best-caseRealTimeLatency').text
            dictLatency['worst_time_latency'] = latency_info.find('Worst-caseRealTimeLatency').text
            dictLatency['average_time_latency'] = latency_info.find('Average-caseRealTimeLatency').text
            dictLatency['min_interval'] = int(latency_info.find('Interval-min').text)
            dictLatency['max_interval'] = int(latency_info.find('Interval-max').text)
            dictLatency['Latency'] = int(latency_info.find('Average-caseLatency').text)
        else:
            dictLatency['Latency'] = params["LATENCY"][0]  # cannot calculate latency
    else:
        dictLatency['Latency'] = LATENCY  # HLS process failed

    dictPPA['LATENCY'] = dictLatency

    LUT = FF = DSP = BRAM = URAM = F1
    CP = F2
    if os.path.exists(hls_rpt):
        print("[INFO] Reading HLS Prediction report...")
        f_hls = open(hls_rpt, 'r')
        for line in f_hls.readlines():
            if line.startswith('|Total'):
                res = [i for i in line.split('|')]
                BRAM = int(res[2].strip())
                DSP = int(res[3].strip())
                FF = int(res[4].strip())
                LUT = int(res[5].strip())
                URAM = int(res[6].strip())
            elif line.startswith('    |ap_clk  |'):
                res = [i for i in line.split()]
                CP = float(res[-4])
    else:
        print("[INFO] HLS Flow Faild !")
        fail_flag = True
    dictPPA['HLS'] = {'LUT': LUT, 'FF': FF, 'DSP': DSP, 'BRAM': BRAM, 'URAM': URAM, 'CP': CP}
    print("HLS Prediction Results:")
    print("LUT = %d, FF = %d, DSP = %d, BRAM = %d, URAM = %d, CP = %f" % (LUT, FF, DSP, BRAM, URAM, CP))

    return dictPPA, fail_flag


def getPPA(params, rpt_list):

    fail_flag = False
    dictPPA = {}
    hls_rpt = rpt_list[0]
    hls_xml = rpt_list[1]
    syn_rpt = rpt_list[2]
    impl_rpt = rpt_list[3]
    power_rpt = rpt_list[4]

    LATENCY = F4
    dictLatency = {}
    if os.path.exists(hls_xml):
        print("[INFO] Reading Latency Information...")
        xml_parser = read_xml(hls_xml)
        root = get_xml_root(xml_parser)
        perf_info = find_first_node(root, 'PerformanceEstimates')
        latency_info = find_first_node(perf_info, 'SummaryOfOverallLatency')

        if latency_info.find('Best-caseLatency').text != 'undef':
            dictLatency['best_latency'] = int(latency_info.find('Best-caseLatency').text)
            dictLatency['worst_latency'] = int(latency_info.find('Worst-caseLatency').text)
            dictLatency['average_latency'] = int(latency_info.find('Average-caseLatency').text)
            dictLatency['best_time_latency'] = latency_info.find('Best-caseRealTimeLatency').text
            dictLatency['worst_time_latency'] = latency_info.find('Worst-caseRealTimeLatency').text
            dictLatency['average_time_latency'] = latency_info.find('Average-caseRealTimeLatency').text
            dictLatency['min_interval'] = int(latency_info.find('Interval-min').text)
            dictLatency['max_interval'] = int(latency_info.find('Interval-max').text)
            dictLatency['Latency'] = int(latency_info.find('Average-caseLatency').text)
        else:
            dictLatency['Latency'] = params["LATENCY"][0]  # cannot calculate latency
    else:
        dictLatency['Latency'] = LATENCY  # HLS process failed

    dictPPA['LATENCY'] = dictLatency
    print(dictLatency)

    LUT = FF = DSP = BRAM = URAM = F1
    CP = F2
    if os.path.exists(hls_rpt):
        print("[INFO] Reading HLS Prediction report...")
        f_hls = open(hls_rpt, 'r')
        for line in f_hls.readlines():
            if line.startswith('|Total'):
                res = [i for i in line.split('|')]
                BRAM = int(res[2].strip())
                DSP = int(res[3].strip())
                FF = int(res[4].strip())
                LUT = int(res[5].strip())
                URAM = int(res[6].strip())
            elif line.startswith('    |ap_clk  |'):
                res = [i for i in line.split()]
                CP = float(res[-4])
    else:
        print("[INFO] HLS Flow Faild !")
        fail_flag = True
    dictPPA['HLS'] = {'LUT': LUT, 'FF': FF, 'DSP': DSP, 'BRAM': BRAM, 'URAM': URAM, 'CP': CP}
    print("HLS Prediction Results:")
    print("LUT = %d, FF = %d, DSP = %d, BRAM = %d, URAM = %d, CP = %f" % (LUT, FF, DSP, BRAM, URAM, CP))

    LUT = FF = DSP = BRAM = URAM = SRL = F1
    CP = F2
    if os.path.exists(syn_rpt):
        print("[INFO] Reading RTL Synthesis report...")
        f_syn = open(syn_rpt, 'r')
        for line in f_syn.readlines():
            res = [i for i in line.split() if i.isdigit()]
            if line.startswith('LUT'):
                LUT = int(res[0])
            elif line.startswith('FF'):
                FF = int(res[0])
            elif line.startswith('DSP'):
                DSP = int(res[0])
            elif line.startswith('BRAM'):
                BRAM = int(res[0])
            elif line.startswith('URAM'):
                URAM = int(res[0])
            elif line.startswith('SRL'):
                SRL = int(res[0])
            elif line.startswith('| Post-Route |'):  # Vitis 2022.1
                # elif line.startswith('| Post-Synthesis |'):  # Vitis 2023.1
                res = [i for i in line.split()]
                CP = float(res[-2])
    else:
        print("[INFO] Synthesis Flow Faild !")
        fail_flag = True
    dictPPA['SYN'] = {'LUT': LUT, 'FF': FF, 'DSP': DSP, 'BRAM': BRAM, 'URAM': URAM, 'SRL': SRL, 'CP': CP}
    print("RTL Synthesis Results:")
    print("LUT = %d, FF = %d, DSP = %d, BRAM = %d, URAM = %d, SRL = %d, CP = %f" % (LUT, FF, DSP, BRAM, URAM, SRL, CP))

    LUT = FF = DSP = BRAM = URAM = SRL = F1
    CP = F2
    PWR = F3
    if os.path.exists(impl_rpt):
        print("[INFO] Reading post-implementation report...")
        f_impl = open(impl_rpt, 'r')
        for line in f_impl.readlines():
            res = [i for i in line.split() if i.isdigit()]
            if line.startswith('LUT'):
                LUT = int(res[0])
            elif line.startswith('FF'):
                FF = int(res[0])
            elif line.startswith('DSP'):
                DSP = int(res[0])
            elif line.startswith('BRAM'):
                BRAM = int(res[0])
            elif line.startswith('URAM'):
                URAM = int(res[0])
            elif line.startswith('SRL'):
                SRL = int(res[0])
            elif line.startswith('CP achieved post-implementation'):
                res = [i for i in line.split()]
                CP = float(res[-1])
    if os.path.exists(power_rpt):
        f_power = open(power_rpt, 'r')
        for line in f_power.readlines():
            if line.startswith("| Total On-Chip Power (W)  |"):
                res = [i for i in line.split()]
                PWR = float(res[-2])
                break
    else:
        print("Implementation Flow Failed !")
        fail_flag = True
    dictPPA['IMPL'] = {'LUT': LUT, 'FF': FF, 'DSP': DSP, 'BRAM': BRAM, 'URAM': URAM, 'SRL': SRL, 'CP': CP, 'PWR': PWR}
    print("Post-Implementation Results:")
    print("LUT = %d, FF = %d, DSP = %d, BRAM = %d, URAM = %d, SRL = %d, CP = %f, PWR = %f" % (LUT, FF, DSP, BRAM, URAM,
                                                                                              SRL, CP, PWR))
    return dictPPA, fail_flag


def normalizePLCA(params, dictPPA):
    wght = [WLUT, WFF, WDSP, WBRAM]
    POW = float(params["POW"][0])
    LTC = float(params["LATENCY"][0])
    CLK = float(params["CLK"][0])
    RU = [float(params["LUT"][0]), float(params["FF"][0]), float(params["DSP"][0]), float(params["BRAM"][0])]
    NUM = sum(np.multiply(wght, RU))
    power = dictPPA['IMPL']['PWR']
    lat = dictPPA['LATENCY']['Latency']
    cp = dictPPA['IMPL']['CP']
    usg = [dictPPA['IMPL']['LUT'], dictPPA['IMPL']['FF'], dictPPA['IMPL']['DSP'], dictPPA['IMPL']['BRAM']]
    area = sum(np.multiply(wght, usg))
    # normalize plca
    npower = power / POW
    nlat = lat / LTC
    ncp = cp / CLK
    narea = area / NUM
    return npower, nlat, ncp, narea


def normalizePCA(params, dictPPA):
    wght = [WLUT, WFF, WDSP, WBRAM]
    POW = float(params["POW"][0])
    CLK = float(params["CLK"][0])
    RU = [float(params["LUT"][0]), float(params["FF"][0]), float(params["DSP"][0]), float(params["BRAM"][0])]
    NUM = sum(np.multiply(wght, RU))
    power = dictPPA['IMPL']['PWR']
    cp = dictPPA['IMPL']['CP']
    usg = [dictPPA['IMPL']['LUT'], dictPPA['IMPL']['FF'], dictPPA['IMPL']['DSP'], dictPPA['IMPL']['BRAM']]
    area = sum(np.multiply(wght, usg))
    # normalize pca
    npower = power / POW
    ncp = cp / CLK
    narea = area / NUM
    return npower, ncp, narea
