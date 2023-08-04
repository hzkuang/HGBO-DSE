import os
from pred.pred_lut import lut_pred
from pred.pred_ff import ff_pred
from pred.pred_dsp import dsp_pred
from pred.pred_bram import bram_pred
from pred.pred_cp import cp_pred
from pred.pred_pwr import pwr_pred
from pred.df_construct import *

top_list = ['aes256_encrypt_ecb', 'bfs', 'fft', 'gemm', 'md_kernel', 'needwun', 'ss_sort', 'ellpack',
            'stencil3d', 'viterbi']

# General node features
n_num_items = ['m_delay', 'latency', 'bitwidth', 'lut', 'ff', 'dsp']
n_num_items_cp = ['m_delay', 'latency']


def get_idx(case):
    if case == 'aes':
        idx_b = 0
    elif case == 'bfs':
        idx_b = 1
    elif case == 'fft':
        idx_b = 2
    elif case == 'gemm':
        idx_b = 3
    elif case == 'md':
        idx_b = 4
    elif case == 'nw':
        idx_b = 5
    elif case == 'sort':
        idx_b = 6
    elif case == 'spmv':
        idx_b = 7
    elif case == 'stencil':
        idx_b = 8
    elif case == 'viterbi':
        idx_b = 9
    else:
        print('Unknown case!')
        idx_b = None
    return idx_b


def getGNNPred(prj_path, hls_attr, case):

    dictIMPL = dict()

    myIRfolder = os.path.join(prj_path, 'graph')
    mySavePath = os.path.join(prj_path, 'cdfg')
    if not os.path.isdir(mySavePath):
        os.mkdir(mySavePath)
    idx_b = get_idx(case)
    top_name = top_list[idx_b]  # top function name
    graph = CDFG(myIRfolder, mySavePath, top_name)
    DG = graph.G

    # std
    dot_store_path = os.path.join(mySavePath, 'std.dot')
    df_store_path = os.path.join(mySavePath, 'std.pt')
    std_dot = generate_pyg_dot(DG, dot_store_path, n_num_items)
    std_dot = nx.convert_node_labels_to_integers(std_dot)
    std_dataframe = generate_dataframe(std_dot, hls_attr, df_store_path)

    # rdc
    dot_store_path = os.path.join(mySavePath, 'rdc.dot')
    df_store_path = os.path.join(mySavePath, 'rdc.pt')
    rdc_dot = generate_pyg_dot(DG, dot_store_path, n_num_items_cp)
    rdc_dot = nx.convert_node_labels_to_integers(rdc_dot)
    rdc_dataframe = generate_dataframe(rdc_dot, [hls_attr[-1]], df_store_path)

    lut = lut_pred(std_dataframe)
    ff = ff_pred(std_dataframe)
    dsp = dsp_pred(std_dataframe)
    bram = bram_pred(std_dataframe)
    cp = cp_pred(rdc_dataframe)
    pwr = pwr_pred(std_dataframe)

    dictIMPL['LUT'] = lut
    dictIMPL['FF'] = ff
    dictIMPL['DSP'] = dsp
    dictIMPL['BRAM'] = bram
    dictIMPL['CP'] = cp
    dictIMPL['PWR'] = pwr

    print(dictIMPL)

    return dictIMPL


# if __name__ == "__main__":
#     prj_path = os.path.abspath('../hgp/data_process/case/bfs/prj_0')
#     hls_attr = [989, 1039, 0, 0, 0, 5.393]
#     getGNNPred(prj_path, hls_attr, 'bfs')
