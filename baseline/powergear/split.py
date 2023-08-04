import argparse
import re


def llvmIR_split(src_path, kernel_name):
    with open('{}/graph/a.o.3.ll'.format(src_path), 'r') as rfile:
        inst_list = rfile.readlines()
    i = 0
    kernel_list = []
    while i < len(inst_list):
        if (re.match('define', inst_list[i]) and re.search(kernel_name, inst_list[i])) or re.match('define internal',
                                                                                                   inst_list[i]):
            kernel = re.search('\@(.+)\(', inst_list[i]).group(1)
            kernel_list.append(kernel)
            for j in range(i+1, len(inst_list)-1):
                if re.match('\}', inst_list[j]):
                    with open('{}/graph/{}.txt'.format(src_path, kernel), 'w') as wfile:
                        for k in range(i, j+1):
                            wfile.write(inst_list[k])
                    break
            i = j
        else:
            i = i + 1
    return kernel_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automatic HLS designs compress script', epilog='')
    parser.add_argument('--src_path', help='directory of hls project as input', action='store')
    parser.add_argument('--kernel', help='directory of hls project as input', action='store')
    args = parser.parse_args()
    kernel_list = llvmIR_split(args.src_path, args.kernel)
    
    for i in range(0, len(kernel_list)):
        if kernel_list[i] == args.kernel:
            del kernel_list[i]
            break
    with open('{}/preprocess/final/kernel.txt'.format(args.src_path), 'w+') as wfile:
        for kernel in kernel_list:
            wfile.write(kernel + ' ')
