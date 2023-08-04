import json
from graph_construct import *
from feature_encode import *
from gen_dataframe import *


# General node features
n_num_items = ['m_delay', 'latency', 'bitwidth', 'lut', 'ff', 'dsp']
n_num_items_cp = ['m_delay', 'latency']

bench_list = ['aes', 'bfs', 'fft', 'gemm', 'md', 'nw', 'sort', 'spmv', 'stencil', 'viterbi']
ver_list = ['aes', 'bulk', 'strided', 'ncubed', 'knn', 'nw', 'radix', 'ellpack', 'stencil3d', 'viterbi']
top_list = ['aes256_encrypt_ecb', 'bfs', 'fft', 'gemm', 'md_kernel', 'needwun', 'ss_sort', 'ellpack',
            'stencil3d', 'viterbi']

root = os.path.abspath('../../dataset')
raw_root = os.path.join(root, 'raw')  # raw HLS dataset path
std_path = os.path.join(root, 'std')  # standard dataset
rdc_path = os.path.join(root, 'rdc')  # reduced dataset

for idx_b in range(len(bench_list)):
    bench_name = bench_list[idx_b]
    bench_ver = ver_list[idx_b]
    print("************************** " + bench_name + " starts processing **************************")
    top_name = top_list[idx_b]  # top function name
    bench = os.path.join(raw_root, bench_name, bench_ver)
    if not os.path.isdir(bench):
        continue
    ppa_path = os.path.join(bench, 'script')
    ppa_json = os.path.join(ppa_path, 'ppa_*.json')
    sample_num = len(glob.glob(ppa_json))
    if sample_num == 0:
        continue
    std_dataframe_list = []
    rdc_dataframe_list = []

    for idx in range(sample_num):
        prj = 'prj_' + str(idx)
        print(prj + ' process...')
        ppa = 'ppa_' + str(idx) + '.json'
        ppa_rpt = os.path.join(ppa_path, ppa)

        myIRfolder = os.path.join(bench, prj, 'graph')
        mySavePath = os.path.join(bench, prj, 'cdfg')
        if not os.path.isdir(myIRfolder):
            continue
        if not os.path.isdir(mySavePath):
            os.mkdir(mySavePath)
        graph = CDFG(myIRfolder, mySavePath, top_name)
        DG = graph.G

        with open(ppa_rpt, 'r') as f:
            ppa_info = json.load(f)
        dict_metric = ppa_info['IMPL']
        lut_value = dict_metric['LUT']
        ff_value = dict_metric['FF']
        cp_value = dict_metric['CP']
        pwr_value = dict_metric['PWR']

        dot_store_path = os.path.join(mySavePath, 'std_pyg_G.dot')
        df_store_path = os.path.join(mySavePath, 'std_pyg_G.pt')
        std_pyg_dot = generate_pyg_dot(DG, dot_store_path, n_num_items)
        std_pyg_dot = nx.convert_node_labels_to_integers(std_pyg_dot)
        dict_hls = ppa_info['HLS']
        metric_list = list(dict_metric.values())
        hls_attr = list(dict_hls.values())
        std_dataframe = generate_dataframe(std_pyg_dot, metric_list, hls_attr, bench_name, prj, df_store_path)
        std_dataframe_list.append(std_dataframe)

        # reduced features for cp
        dot_store_path = os.path.join(mySavePath, 'rdc_pyg_G.dot')
        df_store_path = os.path.join(mySavePath, 'rdc_pyg_G.pt')
        rdc_pyg_dot = generate_pyg_dot(DG, dot_store_path, n_num_items_cp)
        rdc_pyg_dot = nx.convert_node_labels_to_integers(rdc_pyg_dot)
        dict_hls = ppa_info['HLS']
        metric_list = list(dict_metric.values())
        hls_attr = [list(dict_hls.values())[-1]]
        rdc_dataframe = generate_dataframe(rdc_pyg_dot, metric_list, hls_attr, bench_name, prj, df_store_path)
        rdc_dataframe_list.append(rdc_dataframe)

    torch.save(std_dataframe_list, '{a}/{b}.pt'.format(a=std_path, b=bench_name))
    torch.save(rdc_dataframe_list, '{a}/{b}.pt'.format(a=rdc_path, b=bench_name))
