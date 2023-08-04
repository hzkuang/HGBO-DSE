import re
import os
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automatic HLS designs compress script', epilog='')
    parser.add_argument('kernel_name', help='kernel name to process')
    parser.add_argument('--in_dir', help='directory of hls project as input', action='store')

    args = parser.parse_args()
    kernel_name = args.kernel_name
    prj_dir = args.in_dir
    prj_list = os.walk('{}'.format(prj_dir)).__next__()[1]
    prj_list = sorted(prj_list)

    for prj_name in prj_list:
        print(prj_name)
        os.system('cp {a}/{b}/report/{c}.verbose.rpt.xml {a}/{b}/graph'.format(a=prj_dir, b=prj_name, c=kernel_name))
        os.system('llvm-dis {a}/{b}/graph/a.o.3.bc -o {a}/{b}/graph/a.o.3.ll'.format(a=prj_dir, b=prj_name))
        os.system('mkdir {a}/{b}/preprocess'.format(a=prj_dir, b=prj_name))
        os.system('mkdir {a}/{b}/preprocess/final'.format(a=prj_dir, b=prj_name))
        os.system('python split.py {c} --src_path {a}/{b}'.format(a=prj_dir, b=prj_name, c=kernel_name))
        os.system('python op_extract.py {c} --src_path {a}/{b}/graph --dest_path {a}/{b}/preprocess'.format
                  (a=prj_dir, b=prj_name, c=kernel_name))
        os.system('mkdir {}/{}/ir_revise'.format(prj_dir, prj_name))
        os.system('cp {a}/{b}/preprocess/final/cop_node_dict.txt {a}/{b}/ir_revise'.format(a=prj_dir, b=prj_name))
        os.system('cp {a}/{b}/preprocess/final/cop_edge_dict.txt {a}/{b}/ir_revise'.format(a=prj_dir, b=prj_name))
        with open('{}/{}/preprocess/final/kernel.txt'.format(prj_dir, prj_name), 'r') as rfile:
            kernel = rfile.readline()
            kernel_list = re.split(' ', kernel)
        os.system(
            '/home/xfcao/PowerGear/graph_construction/feature_extraction/ir_revise/build/bin/ir_revise '
            '{a} {c}/{b}/graph/a.o.3.bc {c}/{b}/ir_revise/annotated_node.bc {c}/{b}/preprocess/final/'
            'cop_node_dict.txt {c}/{b}/ir_revise/operand_info.txt 2> {c}/{b}/ir_revise/log_ir_revise.txt'.format
            (a=kernel_name, b=prj_name, c=prj_dir))
        for sub_kernel in kernel_list:
            if sub_kernel == '':
                continue
            os.system(
                '/home/xfcao/PowerGear/graph_construction/feature_extraction/ir_revise/build/bin/ir_revise '
                '{a} {c}/{b}/ir_revise/annotated_node.bc {c}/{b}/ir_revise/annotated_node.bc {c}/{b}/preprocess/'
                'final/cop_node_dict.txt {c}/{b}/ir_revise/operand_info.txt 2> {c}/{b}/ir_revise/log_ir_revise.txt'
                .format(
                    a=sub_kernel, b=prj_name, c=prj_dir))
        os.system(
            '/home/xfcao/PowerGear/graph_construction/feature_extraction/ir_revise/build/bin/ir_revise {a} {c}/{b}/'
            'graph/a.o.3.bc {c}/{b}/ir_revise/annotated_edge.bc {c}/{b}/preprocess/final/cop_edge_dict.txt {c}/{b}/'
            'ir_revise/operand_info.txt 2> {c}/{b}/ir_revise/log_ir_edge_revise.txt'.format(
                a=kernel_name, b=prj_name, c=prj_dir))
        for sub_kernel in kernel_list:
            if sub_kernel == '':
                continue
            os.system(
                '/home/xfcao/PowerGear/graph_construction/feature_extraction/ir_revise/build/bin/ir_revise {a} '
                '{c}/{b}/ir_revise/annotated_edge.bc {c}/{b}/ir_revise/annotated_edge.bc {c}/{b}/preprocess/final/'
                'cop_edge_dict.txt {c}/{b}/ir_revise/operand_info.txt 2> {c}/{b}/ir_revise/log_ir_edge_revise.txt'
                .format(
                    a=sub_kernel, b=prj_name, c=prj_dir))
        os.system(
            'cp /home/xfcao/PowerGear/graph_construction/feature_extraction/act_trace/build/rtlop_tracer.h {}/{}/'
            'act_trace'.format(
                prj_dir, prj_name))
        os.system(
            'cp /home/xfcao/PowerGear/graph_construction/feature_extraction/act_trace/build/tracer.h {}/{}/'
            'act_trace'.format(
                prj_dir, prj_name))
        os.system('clang++ -fPIC -c {a}/{b}/ir_revise/annotated_node.bc -o {a}/{b}/act_trace/annotated_node.o'.format
                  (a=prj_dir, b=prj_name))
        os.system(
            '/usr/bin/c++ -fopenmp -O3 -fPIC -std=c++11 -o {a}/{b}/act_trace/main.o -c {a}/{b}/act_trace/'
            'stencil_test.c'.format(
                a=prj_dir, b=prj_name, c=kernel_name))
        os.system(
            '/usr/bin/c++ -fopenmp -O3 -fPIC -std=c++11 -o {a}/{b}/act_trace/act_trace {a}/{b}/act_trace/main.o '
            '{a}/{b}/act_trace/annotated_node.o /home/xfcao/PowerGear/graph_construction/feature_extraction/'
            'act_trace/build/rtlop_tracer.o /home/xfcao/PowerGear/graph_construction/feature_extraction/act_trace/'
            'build/tracer.o'.format(
                a=prj_dir, b=prj_name))
        os.system(
            '{a}/{b}/act_trace/act_trace {a}/{b}/act_trace node > {a}/{b}/act_trace/act_trace.log'.format(a=prj_dir,
                                                                                                          b=prj_name))
        os.system('clang++ -fPIC -c {a}/{b}/ir_revise/annotated_edge.bc -o {a}/{b}/act_trace/annotated_edge.o'.format(
            a=prj_dir, b=prj_name))

        os.system(
            '/usr/bin/c++ -fopenmp -O3 -fPIC -std=c++11 -o {a}/{b}/act_trace/act_trace {a}/{b}/act_trace/main.o '
            '{a}/{b}/act_trace/annotated_edge.o /home/xfcao/PowerGear/graph_construction/feature_extraction/'
            'act_trace/build/rtlop_tracer.o /home/xfcao/PowerGear/graph_construction/feature_extraction/act_trace/'
            'build/tracer.o'.format(
                a=prj_dir, b=prj_name))
        os.system('{a}/{b}/act_trace/act_trace {a}/{b}/act_trace edge > {a}/{b}/act_trace/act_trace.log'.format
                  (a=prj_dir, b=prj_name))

        src_path = '{}/{}/preprocess'.format(prj_dir, prj_name)
        dest_path = '{}/{}/graph'.format(prj_dir, prj_name)
        os.system('python feature_embed.py {} --src_path {} --dest_path {}'.format
                  (args.kernel_name, src_path, dest_path))
