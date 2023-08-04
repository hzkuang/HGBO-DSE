import csv
import os
import re
import argparse
import xml.etree.ElementTree as ET
import networkx as nx
import graphviz as gvz
from operator import itemgetter
from collections import defaultdict


kernel_list = list()
INVOCATION_NUM = 8  # number of kernel invocations in a c main function
PLOT_EDGE_LIMIT = 400

iarith_opcode = ['add', 'sub', 'mul', 'div', 'sqrt']
farith_opcode = ['fadd', 'fsub', 'fmul', 'fdiv', 'fsqrt']
darith_opcode = ['dadd', 'dsub', 'dmul', 'ddiv']
arith_opcode = iarith_opcode + farith_opcode + darith_opcode
logic_opcode = ['icmp', 'fcmp', 'and', 'or', 'xor', 'lshr', 'shl']
arbit_opcode = ['mux', 'select']
mem_opcode = ['store', 'load']

# for the purpose of adding dummy nodes
# 'write', 'store' and 'load' only trace the output operand, no need to take care here
# 'mux' and 'select' have variable op num, no need to consider here
opnd_num_dict = {'add': 3, 'sub': 3, 'mul': 3, 'div': 3, 'sqrt': 2,
                 'fadd': 3, 'fsub': 3, 'fmul': 3, 'fdiv': 3, 'fsqrt': 2,
                 'icmp': 3, 'fcmp': 3, 'and': 3, 'or': 3, 'xor': 3}

bypass_opcode_set = ['const', 'load', 'store', 'reg', 'zext', 'alloca', 'getelementptr', 'bitconcatenate',
                     'partselect', 'trunc', 'sext', 'and', 'or', 'xor', 'phi', 'icmp', 'fcmp']


###################################################################
class cdfg_node:
    def __init__(self, nodeid, name, rtl_name, opcode, bitwidth, m_delay, line_num):
        self.nodeid = nodeid
        self.name = name
        if rtl_name is None:
            self.rtl_name = 'not_exist'
        else:
            self.rtl_name = rtl_name
        self.opcode = opcode
        if bitwidth is None:
            self.bitwidth = 0
        else:
            self.bitwidth = bitwidth
        if m_delay is None:
            self.m_delay = 0
        else:
            self.m_delay = m_delay
        if line_num is None:
            self.line_num = -1
        else:
            self.line_num = line_num


def get_cdfg_node(IRinfo, nodeid_max):
    cdfg_node_dict = dict()
    op_set = set()
    for IRinfo in IRinfo.iter('cdfg'):
        for item in IRinfo.iter('item'):
            if item.find('Value') is not None and item.find('opcode') is not None:
                node_obj = item.find('Value').find('Obj')
                opcode = item.find('opcode').text
                nodeid = int(node_obj.find('id').text) + int(nodeid_max)
                name = node_obj.find('name').text
                rtl_name = node_obj.find('rtlName').text
                if opcode in ['dadd', 'dsub', 'dmul', 'fadd', 'fsub', 'fmul', 'ddiv', 'fdiv'] and rtl_name is None:
                    rtl_name = node_obj.find('coreName').text
                if item.find('Value').find('bitwidth') is not None:
                    bitwidth = item.find('Value').find('bitwidth').text
                else:
                    bitwidth = 0

                if item.find('m_delay') is not None:
                    m_delay = item.find('m_delay').text
                else:
                    m_delay = 0

                if node_obj.find('lineNumber') is not None:
                    line_num = node_obj.find('lineNumber').text
                else:
                    line_num = -1

                cdfg_node_dict[nodeid] = cdfg_node(nodeid, name, rtl_name, opcode, bitwidth, m_delay, line_num)
                op_set.add(opcode)

    return cdfg_node_dict, sorted(list(op_set))


def get_nodeid_max(cdfg_fsm_node_dict):
    nodeid_max = 0
    for nodeid in cdfg_fsm_node_dict:
        if int(nodeid) > nodeid_max:
            nodeid_max = int(nodeid)
    return nodeid_max


def cdfg_node_explore(info_dir, IRinfo, kernel_name, nodeid_max):
    cdfg_node_dict, op_set = get_cdfg_node(IRinfo, nodeid_max)

    with open('{}/{}/cdfg_node_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        title = ['nodeid', 'name', 'rtl_name', 'opcode', 'bitwidth', 'm_delay', 'line_num']
        writer.writerow(title)
        for nodeid in cdfg_node_dict:
            node_objs = cdfg_node_dict[nodeid]
            wr_line = [node_objs.nodeid, node_objs.name, node_objs.rtl_name, node_objs.opcode, node_objs.bitwidth,
                       node_objs.m_delay, node_objs.line_num]
            writer.writerow(wr_line)

    with open('{}/{}/op_set.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        for opcode in op_set:
            wr_line = [opcode]
            writer.writerow(wr_line)

    return cdfg_node_dict, op_set


###################################################################
class fsm_node:
    def __init__(self, opid, nodeid, c_step, stage, latency, instruction, opnd_num, bw_out, bw_0, bw_1, bw_2):
        self.opid = opid
        self.nodeid = nodeid
        self.c_step = c_step
        self.stage = stage
        self.latency = latency
        self.instruction = instruction
        if bw_out is None:
            self.bw_out = 0
        else:
            self.bw_out = bw_out
        if bw_0 is None:
            self.bw_0 = 0
        else:
            self.bw_0 = bw_0
        if bw_1 is None:
            self.bw_1 = 0
        else:
            self.bw_1 = bw_1
        if bw_2 is None:
            self.bw_2 = 0
        else:
            self.bw_2 = bw_2
        if opnd_num is None:
            self.opnd_num = 0
        else:
            self.opnd_num = opnd_num

        self.rtl_name = ''
        self.opcode = ''
        self.from_node_set = set()
        self.to_node_set = set()


class port_node:
    def __init__(self, portid, name, direction, mem_type):
        self.portid = portid
        self.name = name
        self.direction = direction
        self.mem_type = mem_type


class df_trace_node:
    def __init__(self, src_name, src_opid, dst_name, dst_opid):
        self.src_name = src_name
        self.src_opid = src_opid
        self.dst_name = dst_name
        self.dst_opid = dst_opid


def get_fsm_node(FSMDinfo, nodeid_max):
    fsm_node_dict = dict()
    op_node_mapping_dict = dict()
    for op in FSMDinfo.iter('operation'):
        opid = int(op.get('id'))
        c_step = op.get('st_id')
        stage = op.get('stage')
        latency = op.get('lat')

        node_list = op.findall('Node')
        for node in node_list:
            nodeid = int(node.get('id')) + int(nodeid_max)
            instruction = node.text.strip().partition(' ')[2].strip()
            bw_out = node.get('bw')
            bw_0 = node.get('op_0_bw')
            bw_1 = node.get('op_1_bw')
            bw_2 = node.get('op_2_bw')
            opnd_num = len(node.attrib) - 1
            if nodeid not in fsm_node_dict:
                fsm_node_dict[nodeid] = fsm_node(opid, nodeid, c_step, stage, latency, instruction, opnd_num, bw_out,
                                                 bw_0, bw_1, bw_2)
            if opid not in op_node_mapping_dict:
                op_node_mapping_dict[opid] = nodeid
            else:
                print("CHECK: the same opid ({}) exists multiple times in FSMDinfo".format(opid))
    return fsm_node_dict, op_node_mapping_dict


def get_fsm_port(FSMDinfo):
    port_dict = dict()
    for port in FSMDinfo.iter('port'):
        portid = int(port.get('id'))
        port_name = port.get('name')
        direction = port.get('dir')
        mem_type = port.find('core').text
        port_dict[portid] = port_node(int(portid), port_name, direction, mem_type)
    return port_dict


def get_df_trace(FSMDinfo):
    df_trace_dict = dict()
    for dataflow in FSMDinfo.iter('dataflow'):
        src_name = dataflow.get('from')
        src_opid = int(dataflow.get('fromId'))
        dst_name = dataflow.get('to')
        dst_opid = int(dataflow.get('toId'))
        if dst_opid not in df_trace_dict:
            df_trace_dict[dst_opid] = list()
        df_trace_dict[dst_opid].append(df_trace_node(src_name, src_opid, dst_name, dst_opid))
    return df_trace_dict


def fsm_node_trace(fsm_node_dict, op_node_mapping_dict, df_trace_dict):
    for dst_opid in df_trace_dict:
        for df_node in df_trace_dict[dst_opid]:
            src_opid = df_node.src_opid
            if src_opid in op_node_mapping_dict and dst_opid in op_node_mapping_dict:
                from_nodeid = op_node_mapping_dict[src_opid]
                to_nodeid = op_node_mapping_dict[dst_opid]
                fsm_node_dict[from_nodeid].to_node_set.add(to_nodeid)
                fsm_node_dict[to_nodeid].from_node_set.add(from_nodeid)


def fsm_node_explore(info_dir, FSMDinfo, kernel_name, nodeid_max):
    fsm_node_dict, op_node_mapping_dict = get_fsm_node(FSMDinfo, nodeid_max)
    port_dict = get_fsm_port(FSMDinfo)
    df_trace_dict = get_df_trace(FSMDinfo)
    fsm_node_trace(fsm_node_dict, op_node_mapping_dict, df_trace_dict)

    with open('{}/{}/fsm_node_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        title = ['opid', 'nodeid', 'c_step', 'stage', 'latency', 'opnd_num', 'bw_out', 'bw_0', 'bw_1', 'bw_2',
                 'from_node_set', 'to_node_set', 'instruction']
        writer.writerow(title)
        for nodeid in fsm_node_dict:
            node = fsm_node_dict[nodeid]
            wr_line = [node.opid, node.nodeid, node.c_step, node.stage, node.latency, node.opnd_num, node.bw_out,
                       node.bw_0, node.bw_1, node.bw_2,
                       str(sorted(node.from_node_set)).strip('[]'), str(sorted(node.to_node_set)).strip('[]'),
                       node.instruction]
            writer.writerow(wr_line)

    with open('{}/{}/port_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        title = ['portid', 'name', 'direction', 'mem_type']
        writer.writerow(title)
        for pid in port_dict:
            pnode = port_dict[pid]
            wr_line = [pnode.portid, pnode.name, pnode.direction, pnode.mem_type]
            writer.writerow(wr_line)

    return fsm_node_dict, op_node_mapping_dict


###################################################################
class cdfg_fsm_node:
    def __init__(self, nodeid, name, rtl_name, opcode, line_num, opid, c_step, latency, instruction, opnd_num, bw_out,
                 bw_0, bw_1, bw_2, m_delay, from_node_set, to_node_set):
        self.nodeid = nodeid
        self.name = name
        self.rtl_name = rtl_name
        self.opcode = opcode
        self.line_num = line_num
        self.opid = opid
        self.c_step = c_step
        self.latency = latency
        self.instruction = instruction
        self.opnd_num = opnd_num
        self.bw_out = bw_out
        self.bw_0 = bw_0
        self.bw_1 = bw_1
        self.bw_2 = bw_2
        self.m_delay = m_delay
        self.from_node_set = from_node_set
        self.to_node_set = to_node_set


def get_cdfg_fsm_node(cdfg_node_dict, fsm_node_dict):
    cdfg_fsm_node_dict = dict()
    for nodeid in cdfg_node_dict:
        if cdfg_node_dict[nodeid].opcode == 'call':
            inst = fsm_node_dict[nodeid].instruction
            kernel_name = re.split(' @|, ', inst)[1]

            kernel_list.append(kernel_name)
        if nodeid in fsm_node_dict:
            node = cdfg_node_dict[nodeid]
            cop = fsm_node_dict[nodeid]
            cdfg_fsm_node_dict[nodeid] = cdfg_fsm_node(nodeid, node.name, node.rtl_name, node.opcode, node.line_num,
                                                       cop.opid, cop.c_step, cop.latency, cop.instruction,
                                                       cop.opnd_num, cop.bw_out, cop.bw_0, cop.bw_1, cop.bw_2,
                                                       node.m_delay, cop.from_node_set, cop.to_node_set)

    return cdfg_fsm_node_dict


def cdfg_fsm_node_explore(info_dir, cdfg_node_dict, fsm_node_dict, kernel_name):
    cdfg_fsm_node_dict = get_cdfg_fsm_node(cdfg_node_dict, fsm_node_dict)
    with open('{}/{}/cdfg_fsm_node_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        title = ['nodeid', 'name', 'rtl_name', 'opcode', 'line_num', 'opid', 'c_step', 'latency', 'opnd_num', 'bw_out',
                 'bw_0', 'bw_1', 'bw_2', 'm_delay', 'from_node_set', 'to_node_set', 'instruction']
        writer.writerow(title)
        for nodeid in cdfg_fsm_node_dict:
            node = cdfg_fsm_node_dict[nodeid]
            wr_line = [node.nodeid, node.name, node.rtl_name, node.opcode, node.line_num, node.opid, node.c_step,
                       node.latency, node.opnd_num, node.bw_out, node.bw_0, node.bw_1,
                       node.bw_2, node.m_delay, str(sorted(node.from_node_set)).strip('[]'),
                       str(sorted(node.to_node_set)).strip('[]'), node.instruction]
            writer.writerow(wr_line)

    return cdfg_fsm_node_dict


def get_df_reg(FSMDinfo, op_node_mapping_dict, cdfg_fsm_node_dict):
    df_reg_dict = defaultdict(lambda: defaultdict(tuple))
    for dataflow in FSMDinfo.iter('dataflow'):
        src_name = dataflow.get('from')
        src_opid = int(dataflow.get('fromId'))
        dst_name = dataflow.get('to')
        dst_opid = int(dataflow.get('toId'))

        if src_opid in op_node_mapping_dict and dst_opid in op_node_mapping_dict:
            src_nodeid = op_node_mapping_dict[src_opid]
            dst_nodeid = op_node_mapping_dict[dst_opid]
        else:
            continue

        if not df_reg_dict[src_nodeid][dst_nodeid]:
            if dst_nodeid in cdfg_fsm_node_dict:
                cdfg_fsm_node = cdfg_fsm_node_dict[dst_nodeid]
                if cdfg_fsm_node.opcode == 'store':
                    # for 'store'/'write', need to change the dst_name to the first operand
                    # instead of output = StgVal
                    dst_name = re.split(' |,', cdfg_fsm_node.instruction.strip(''))[2].strip('%')
                elif cdfg_fsm_node.opcode == 'write':
                    dst_name = re.split('%|,', cdfg_fsm_node.instruction.strip(''))[1].strip('%').strip('\)')
            df_reg_dict[src_nodeid][dst_nodeid] = (src_name, dst_name, src_nodeid, dst_nodeid)
        elif df_reg_dict[src_nodeid][dst_nodeid][0] != src_name:
            print('CHECK: multiple src_nodeid = {} to dst_nodeid = {} with different src_name = {}'.format(src_nodeid,
                                                                                                           dst_nodeid,
                                                                                                           src_name))
            assert 0
    return df_reg_dict


###################################################################
class component_rsc:
    def __init__(self, cname, coptype):
        self.cname = cname
        self.coptype = coptype
        self.module = ''
        self.operation = ''
        self.bram_18k = 0
        self.dsp = 0
        self.ff = 0
        self.lut = 0

        self.mem_words = 0
        self.mem_bits = 0
        self.mem_banks = 0
        self.mem_wxbitsxbanks = 0

        self.ff_depth = 0
        self.ff_bits = 0
        self.ff_size = 0

        self.bitwidth_p0 = 0
        self.bitwidth_p1 = 0

        self.mux_inputsize = 0
        self.mux_bits = 0
        self.mux_totalbits = 0

        self.reg_bits = 0
        self.reg_const_bits = 0


def get_rsc_sub(IRinfo):
    rsc_dict = dict()
    for section in IRinfo.iter('res'):
        for component in section.iter('dp_component_resource'):
            for item in component.findall('item'):
                ori_name = item.find('first').text
                name = re.split(' ', ori_name)[0]
                rsc_dict[name] = component_rsc(name, 'instacnce')
                rsc = item.find('second')
                for num in rsc.findall('item'):
                    if num.find('first').text == 'DSP':
                        rsc_dict[name].dsp = int(num.find('second').text)
                    elif num.find('first').text == 'FF':
                        rsc_dict[name].ff = int(num.find('second').text)
                    elif num.find('first').text == 'LUT':
                        rsc_dict[name].lut = int(num.find('second').text)
        for expression in section.iter('dp_expression_resource'):
            for item in expression.findall('item'):
                ori_name = item.find('first').text
                name = re.split(' ', ori_name)[0]
                rsc_dict[name] = component_rsc(name, 'expression')
                rsc = item.find('second')
                for num in rsc.findall('item'):
                    if num.find('first').text == '(0P0)':
                        rsc_dict[name].bitwidth_p0 = int(num.find('second').text)
                    elif num.find('first').text == '(1P1)':
                        rsc_dict[name].bitwidth_p1 = int(num.find('second').text)
                    elif num.find('first').text == 'FF':
                        rsc_dict[name].ff = int(num.find('second').text)
                    elif num.find('first').text == 'LUT':
                        rsc_dict[name].lut = int(num.find('second').text)
        for memory in section.iter('dp_memory_resource'):
            for item in memory.findall('item'):
                ori_name = item.find('first').text
                name = re.split(' ', ori_name)[0]

                rsc_dict[name] = component_rsc(name, 'memory')
                rsc = item.find('second')
                for num in rsc.findall('item'):
                    if num.find('first').text == '(0Words)':
                        rsc_dict[name].mem_words = int(num.find('second').text)
                    elif num.find('first').text == '(1Bits)':
                        rsc_dict[name].mem_bits = int(num.find('second').text)
                    elif num.find('first').text == 'FF':
                        rsc_dict[name].ff = int(num.find('second').text)
                    elif num.find('first').text == 'LUT':
                        rsc_dict[name].lut = int(num.find('second').text)
                    elif num.find('first').text == '(2Banks)':
                        rsc_dict[name].mem_banks = int(num.find('second').text)
                    elif num.find('first').text == '(3W*Bits*Banks)':
                        rsc_dict[name].mem_wxbitsxbanks = int(num.find('second').text)
                    elif num.find('first').text == 'BRAM':
                        rsc_dict[name].bram_18k = int(num.find('second').text)
        for multiplexer in section.iter('dp_multiplexer_resource'):
            for item in multiplexer.findall('item'):
                ori_name = item.find('first').text
                name = re.split(' ', ori_name)[0]
                if name in rsc_dict:
                    rsc_dict[name].coptype = rsc_dict[name].coptype + '_multiplexer'
                else:
                    rsc_dict[name] = component_rsc(name, 'multiplexer')
                rsc = item.find('second')
                for num in rsc.findall('item'):
                    if num.find('first').text == '(0Size)':
                        rsc_dict[name].mux_inputsize = int(num.find('second').text)
                    elif num.find('first').text == '(1Bits)':
                        rsc_dict[name].mux_bits = int(num.find('second').text)
                    elif num.find('first').text == '(2Count)':
                        rsc_dict[name].mux_totalbits = int(num.find('second').text)
                    elif num.find('first').text == 'LUT':
                        rsc_dict[name].lut = int(num.find('second').text)
        for register in section.iter('dp_register_resource'):
            for item in register.findall('item'):
                ori_name = item.find('first').text
                name = re.split(' ', ori_name)[0]
                if name in rsc_dict:
                    rsc_dict[name].coptype = rsc_dict[name].coptype + '_register'
                else:
                    rsc_dict[name] = component_rsc(name, 'register')
                rsc = item.find('second')
                for num in rsc.findall('item'):
                    if num.find('first').text == '(Bits)':
                        rsc_dict[name].reg_bits = int(num.find('second').text)
                    elif num.find('first').text == '(Consts)':
                        rsc_dict[name].reg_const_bits = int(num.find('second').text)
                    elif num.find('first').text == 'FF':
                        rsc_dict[name].ff = int(num.find('second').text)
        for dsp in section.iter('dp_dsp_resource'):
            for item in dsp.findall('item'):
                rtl_name = item.find('first').text
                if int(item.find('second').find('count').text) == 1:
                    rsc_dict[rtl_name] = component_rsc(rtl_name, 'dsp')
                    rsc_dict[rtl_name].dsp = int(item.find('second').find('item').find('second').text)
    return rsc_dict


def get_component_rsc(RSCinfo):  # some components appear in different types, add up in this case
    rsc_dict = dict()
    for section in RSCinfo.findall('section'):
        if section.get('name') == 'Utilization Estimates':
            for item in section.findall('item'):
                if item.get('name') == 'Detail':
                    for subitem in item.find('section').findall('item'):
                        if subitem.get('name') == 'Instance':
                            for column in subitem.iter('column'):
                                name = column.get('name')
                                uti_list = column.text.split(', ')
                                if name in rsc_dict:
                                    rsc_dict[name].coptype = rsc_dict[name].coptype + '_instance'
                                    if rsc_dict[name].module == '':
                                        rsc_dict[name].module = uti_list[0]
                                    else:
                                        rsc_dict[name].module = rsc_dict[name].module + '_' + uti_list[0]
                                else:
                                    rsc_dict[name] = component_rsc(name, 'instance')
                                    rsc_dict[name].module = uti_list[0]

                                rsc_dict[name].bram_18k += int(uti_list[1])
                                rsc_dict[name].dsp += int(uti_list[2])
                                rsc_dict[name].ff += int(uti_list[3])
                                rsc_dict[name].lut += int(uti_list[4])

                        elif subitem.get('name') == 'Memory':
                            for column in subitem.iter('column'):
                                name = column.get('name')
                                uti_list = column.text.split(', ')
                                if name in rsc_dict:
                                    rsc_dict[name].coptype = rsc_dict[name].coptype + '_memory'
                                    if rsc_dict[name].module == '':
                                        rsc_dict[name].module = uti_list[0]
                                    else:
                                        rsc_dict[name].module = rsc_dict[name].module + '_' + uti_list[0]
                                else:
                                    rsc_dict[name] = component_rsc(name, 'memory')
                                    rsc_dict[name].module = uti_list[0]

                                rsc_dict[name].bram_18k += int(uti_list[1])
                                rsc_dict[name].ff += int(uti_list[2])
                                rsc_dict[name].lut += int(uti_list[3])
                                rsc_dict[name].mem_words += int(uti_list[4])
                                rsc_dict[name].mem_bits += int(uti_list[5])
                                rsc_dict[name].mem_banks += int(uti_list[6])
                                rsc_dict[name].mem_wxbitsxbanks += int(uti_list[7])

                        elif subitem.get('name') == 'FIFO':
                            for column in subitem.iter('column'):
                                name = column.get('name')
                                uti_list = column.text.split(', ')
                                if name in rsc_dict:
                                    rsc_dict[name].coptype = rsc_dict[name].coptype + '_fifo'
                                else:
                                    rsc_dict[name] = component_rsc(name, 'memory')

                                rsc_dict[name].bram_18k += int(uti_list[0])
                                rsc_dict[name].ff += int(uti_list[1])
                                rsc_dict[name].lut += int(uti_list[2])
                                rsc_dict[name].ff_depth += int(uti_list[3])
                                rsc_dict[name].ff_bits += int(uti_list[4])
                                rsc_dict[name].ff_size += int(uti_list[5])

                        elif subitem.get('name') == 'Expression':
                            for column in subitem.iter('column'):
                                name = column.get('name')
                                uti_list = column.text.split(', ')
                                if name in rsc_dict:
                                    rsc_dict[name].coptype = rsc_dict[name].coptype + '_expression'
                                    if rsc_dict[name].operation == '':
                                        rsc_dict[name].operation = uti_list[0]
                                    else:
                                        rsc_dict[name].operation = rsc_dict[name].operation + '_' + uti_list[0]
                                else:
                                    rsc_dict[name] = component_rsc(name, 'expression')
                                    rsc_dict[name].operation = uti_list[0]

                                rsc_dict[name].dsp += int(uti_list[1])
                                rsc_dict[name].ff += int(uti_list[2])
                                rsc_dict[name].lut += int(uti_list[3])
                                if int(rsc_dict[name].bitwidth_p0) == 0:
                                    rsc_dict[name].bitwidth_p0 = uti_list[4]
                                else:
                                    rsc_dict[name].bitwidth_p0 = rsc_dict[name].bitwidth_p0 + '_' + uti_list[4]
                                    print('ERROR: check expression bitwidth_p0 {}'.format(name))
                                if int(rsc_dict[name].bitwidth_p1) == 0:
                                    rsc_dict[name].bitwidth_p1 = uti_list[5]
                                else:
                                    rsc_dict[name].bitwidth_p1 = rsc_dict[name].bitwidth_p1 + '_' + uti_list[5]
                                    print('ERROR: check expression bitwidth_p1 {}'.format(name))

                        elif subitem.get('name') == 'Multiplexer':
                            for column in subitem.iter('column'):
                                name = column.get('name')
                                uti_list = column.text.split(', ')
                                if name in rsc_dict:
                                    rsc_dict[name].coptype = rsc_dict[name].coptype + '_multiplexer'
                                else:
                                    rsc_dict[name] = component_rsc(name, 'multiplexer')

                                rsc_dict[name].lut += int(uti_list[0])
                                rsc_dict[name].mux_inputsize += int(uti_list[1])
                                rsc_dict[name].mux_bits += int(uti_list[2])
                                rsc_dict[name].mux_totalbits += int(uti_list[3])

                        elif subitem.get('name') == 'Register':
                            for column in subitem.iter('column'):
                                name = column.get('name')
                                uti_list = column.text.strip().split(', ')
                                if name in rsc_dict:
                                    rsc_dict[name].coptype = rsc_dict[name].coptype + '_register'
                                else:
                                    rsc_dict[name] = component_rsc(name, 'register')

                                rsc_dict[name].ff += int(uti_list[0])
                                rsc_dict[name].lut += int(uti_list[1])
                                rsc_dict[name].reg_bits += int(uti_list[2])
                                rsc_dict[name].reg_const_bits += int(uti_list[3])
    return rsc_dict


def sub_component_rsc_explore(info_dir, IRinfo, kernel_name):
    rsc_dict = get_rsc_sub(IRinfo)

    with open('{}/{}/rsc_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        title = ['name', 'coptype', 'module', 'operation', 'bram_18k', 'dsp', 'ff', 'lut', 'mem_words', 'mem_bits',
                 'mem_banks', 'mem_wxbitsxbanks',
                 'ff_depth', 'ff_bits', 'ff_size', 'bitwidth_p0', 'bitwidth_p1', 'mux_inputsize', 'mux_bits',
                 'mux_totalbits', 'reg_bits', 'reg_const_bits']
        writer.writerow(title)
        for name in rsc_dict:
            component = rsc_dict[name]
            wr_line = [component.cname, component.coptype, component.module, component.operation, component.bram_18k,
                       component.dsp, component.ff, component.lut, component.mem_words, component.mem_bits,
                       component.mem_banks, component.mem_wxbitsxbanks,
                       component.ff_depth, component.ff_bits, component.ff_size, component.bitwidth_p0,
                       component.bitwidth_p1, component.mux_inputsize,
                       component.mux_bits, component.mux_totalbits, component.reg_bits, component.reg_const_bits]
            writer.writerow(wr_line)

    return rsc_dict


def component_rsc_explore(info_dir, RSCinfo, kernel_name):
    rsc_dict = get_component_rsc(RSCinfo)

    with open('{}/{}/rsc_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        title = ['name', 'coptype', 'module', 'operation', 'bram_18k', 'dsp', 'ff', 'lut', 'mem_words', 'mem_bits',
                 'mem_banks', 'mem_wxbitsxbanks',
                 'ff_depth', 'ff_bits', 'ff_size', 'bitwidth_p0', 'bitwidth_p1', 'mux_inputsize', 'mux_bits',
                 'mux_totalbits', 'reg_bits', 'reg_const_bits']
        writer.writerow(title)
        for name in rsc_dict:
            component = rsc_dict[name]
            wr_line = [component.cname, component.coptype, component.module, component.operation, component.bram_18k,
                       component.dsp, component.ff, component.lut, component.mem_words, component.mem_bits,
                       component.mem_banks, component.mem_wxbitsxbanks,
                       component.ff_depth, component.ff_bits, component.ff_size, component.bitwidth_p0,
                       component.bitwidth_p1, component.mux_inputsize,
                       component.mux_bits, component.mux_totalbits, component.reg_bits, component.reg_const_bits]
            writer.writerow(wr_line)

    return rsc_dict


###################################################################
class c_operator:
    def __init__(self, nodeid, name, rtl_id, rtl_name, optype, opcode, line_num, c_step, latency, instruction, opnd_num,
                 bw_out, bw_0, bw_1, bw_2, m_delay):
        self.nodeid = nodeid
        self.name = name
        self.rtl_id = rtl_id
        self.rtl_name = rtl_name
        self.optype = optype
        self.opcode = opcode
        self.line_num = line_num
        self.c_step = c_step
        self.latency = latency
        self.instruction = instruction
        self.opnd_num = opnd_num
        self.bw_out = bw_out
        self.bw_0 = bw_0
        self.bw_1 = bw_1
        self.bw_2 = bw_2
        self.m_delay = m_delay


class rtl_operator:
    def __init__(self, rtl_name, rtl_id, opnd_num, bw_out, bw_0, bw_1, bw_2, optype, opcode, delay):
        self.rtl_name = rtl_name
        self.rtl_id = rtl_id
        self.reg_name = []
        self.opnd_num = opnd_num
        self.bw_out = bw_out
        self.bw_0 = bw_0
        self.bw_1 = bw_1
        self.bw_2 = bw_2
        self.lut = 0
        self.dsp = 0
        self.bram = 0
        self.ff = 0

        self.optype = optype  # arith/logic/memory/aribit
        self.opcode = opcode
        self.cop_set = set()
        self.line_num_set = set()
        self.comp_name = 'not_exist'
        self.latency_set = set()
        self.latency = 0
        self.delay = delay

    def add_reg_name(self, reg_name):
        self.reg_name.append(reg_name)

    def add_cop(self, cop):
        self.cop_set.add(cop)

    def add_line_num(self, line_num):
        self.line_num_set.add(line_num)

    def add_latency(self, lat):
        self.latency_set.add(lat)
        self.latency = sum(list(self.latency_set)) / len(list(self.latency_set))


def get_arith_logic_arbit_op(cdfg_fsm_node_dict, rsc_dict, cop_dict, rop_dict, rtl_id):
    for nodeid in cdfg_fsm_node_dict:
        node = cdfg_fsm_node_dict[nodeid]
        if (node.opcode in arith_opcode) or (node.opcode in arbit_opcode) or (
                node.opcode in logic_opcode):  # arithmetic/arbit/logic operators
            if node.opcode in arith_opcode:
                optype = 'arith'
            elif node.opcode in logic_opcode:
                optype = 'logic'
            elif node.opcode in arbit_opcode:
                optype = 'arbit'

            if node.rtl_name in rop_dict:
                rop_dict[node.rtl_name].add_cop(int(nodeid))
                rop_dict[node.rtl_name].add_line_num(int(node.line_num))
                rop_dict[node.rtl_name].add_latency(int(node.latency))
                if node.opcode not in rop_dict[node.rtl_name].opcode:
                    rop_dict[node.rtl_name].opcode = rop_dict[node.rtl_name].opcode + '_' + node.opcode
                if not rop_dict[node.rtl_name].optype == optype:
                    print('CHECK: one rtl_name ({}) has multiple optypes: {} and {}.'.format(node.rtl_name, rop_dict[
                        node.rtl_name].optype, optype))
                if rop_dict[node.rtl_name].delay != node.m_delay:
                    print('CHECK: rtl_name ({}) has multiple delay values: {} and {}.'.format(node.rtl_name, rop_dict[
                        node.rtl_name].delay, node.m_delay))

                cop_dict[nodeid] = c_operator(node.nodeid, node.name, rop_dict[node.rtl_name].rtl_id, node.rtl_name,
                                              optype, node.opcode, node.line_num,
                                              node.c_step, node.latency, node.instruction, node.opnd_num, node.bw_out,
                                              node.bw_0, node.bw_1, node.bw_2, node.m_delay)
            else:
                rop_dict[node.rtl_name] = rtl_operator(node.rtl_name, rtl_id, node.opnd_num, node.bw_out, node.bw_0,
                                                       node.bw_1, node.bw_2,
                                                       optype, node.opcode, node.m_delay)
                cop_dict[nodeid] = c_operator(node.nodeid, node.name, rtl_id, node.rtl_name, optype, node.opcode,
                                              node.line_num, node.c_step,
                                              node.latency, node.instruction, node.opnd_num, node.bw_out, node.bw_0,
                                              node.bw_1, node.bw_2, node.m_delay)
                rtl_id = rtl_id + 1
                if node.rtl_name not in rsc_dict:
                    print('CHECK: node.rtl_name ({}) not in rsc_dict, may be simple operation'.format(node.rtl_name))
                    rop_dict[node.rtl_name].add_cop(int(nodeid))
                    rop_dict[node.rtl_name].add_line_num(int(node.line_num))
                    rop_dict[node.rtl_name].add_latency(int(node.latency))
                    if node.rtl_name == 'DAddSub_fulldsp':
                        rop_dict[node.rtl_name].lut = 782
                        rop_dict[node.rtl_name].dsp = 3
                        rop_dict[node.rtl_name].bram = 0
                        rop_dict[node.rtl_name].ff = 445

                    if node.rtl_name == 'DMul_fulldsp':
                        rop_dict[node.rtl_name].lut = 213
                        rop_dict[node.rtl_name].dsp = 10
                        rop_dict[node.rtl_name].bram = 0
                        rop_dict[node.rtl_name].ff = 282

                    if node.rtl_name == 'DMul_maxdsp':
                        rop_dict[node.rtl_name].lut = 203
                        rop_dict[node.rtl_name].dsp = 11
                        rop_dict[node.rtl_name].bram = 0
                        rop_dict[node.rtl_name].ff = 299

                    if node.rtl_name == 'DAddSub_nodsp':
                        rop_dict[node.rtl_name].lut = 810
                        rop_dict[node.rtl_name].dsp = 0
                        rop_dict[node.rtl_name].bram = 0
                        rop_dict[node.rtl_name].ff = 328

                    if node.rtl_name == 'DMul_nodsp':
                        rop_dict[node.rtl_name].lut = 2641
                        rop_dict[node.rtl_name].dsp = 0
                        rop_dict[node.rtl_name].bram = 0
                        rop_dict[node.rtl_name].ff = 477

                    continue
                rop_dict[node.rtl_name].lut = rsc_dict[node.rtl_name].lut
                rop_dict[node.rtl_name].dsp = rsc_dict[node.rtl_name].dsp
                rop_dict[node.rtl_name].bram = rsc_dict[node.rtl_name].bram_18k
                rop_dict[node.rtl_name].ff = rsc_dict[node.rtl_name].ff
                rop_dict[node.rtl_name].add_cop(int(nodeid))
                rop_dict[node.rtl_name].add_line_num(int(node.line_num))
                rop_dict[node.rtl_name].add_latency(int(node.latency))
                if (node.opcode in iarith_opcode) or (node.opcode in arbit_opcode) or (node.opcode in logic_opcode):
                    if 'expression' in rsc_dict[node.rtl_name].coptype:
                        rop_dict[node.rtl_name].bw_0 = rsc_dict[node.rtl_name].bitwidth_p0
                        rop_dict[node.rtl_name].bw_1 = rsc_dict[node.rtl_name].bitwidth_p1

            if node.rtl_name == 'not_exist':
                print('CHECK: node.rtl_name ({}) does not exist.'.format(nodeid))

    return rtl_id


def get_mem_op(IRinfo, cdfg_fsm_node_dict, rsc_dict, cop_dict, rop_dict, rtl_id, nodeid_max):
    optype = 'memory'
    for nodeid in cdfg_fsm_node_dict:
        if cdfg_fsm_node_dict[nodeid].opcode in ['alloca', 'getelementptr']:
            rtl_name = cdfg_fsm_node_dict[nodeid].name
            to_node_list = list(cdfg_fsm_node_dict[nodeid].to_node_set)
            for nodeid2 in to_node_list:
                if nodeid2 in cdfg_fsm_node_dict:
                    if cdfg_fsm_node_dict[nodeid2].opcode in ['load', 'store']:
                        node = cdfg_fsm_node_dict[nodeid2]
                        if rtl_name in rop_dict:
                            rop_dict[rtl_name].add_cop(int(nodeid))
                            rop_dict[rtl_name].add_line_num(int(node.line_num))
                            rop_dict[rtl_name].add_latency(int(node.latency))
                            if node.opcode not in rop_dict[rtl_name].opcode:
                                rop_dict[rtl_name].opcode = rop_dict[rtl_name].opcode + '_' + node.opcode
                            if not rop_dict[rtl_name].optype == optype:
                                print('CHECK: one rtl_name ({}) has multiple optypes: {} and {}.'.format
                                      (rtl_name, rop_dict[rtl_name].optype, optype))

                            cop_dict[nodeid2] = c_operator(node.nodeid, node.name, rop_dict[rtl_name].rtl_id, rtl_name,
                                                           optype, node.opcode, node.line_num, node.c_step,
                                                           node.latency, node.instruction, node.opnd_num, node.bw_out,
                                                           node.bw_0, node.bw_1, node.bw_2, node.m_delay)
                        else:
                            rop_dict[rtl_name] = rtl_operator(rtl_name, rtl_id, node.bw_out, node.opnd_num, node.bw_0,
                                                              node.bw_1, node.bw_2,
                                                              optype, node.opcode, node.m_delay)
                            rop_dict[rtl_name].add_cop(int(nodeid))
                            rop_dict[rtl_name].add_line_num(int(node.line_num))
                            rop_dict[rtl_name].add_latency(int(node.latency))
                            cop_dict[nodeid2] = c_operator(node.nodeid, node.name, rtl_id, rtl_name, optype,
                                                           node.opcode, node.line_num, node.c_step,
                                                           node.latency, node.instruction, node.opnd_num, node.bw_out,
                                                           node.bw_0, node.bw_1, node.bw_2, node.m_delay)
                            rtl_id = rtl_id + 1
        if cdfg_fsm_node_dict[nodeid].opcode in ['read', 'write']:
            rtl_name = cdfg_fsm_node_dict[nodeid].name
            node = cdfg_fsm_node_dict[nodeid]
            if rtl_name in rop_dict:
                rop_dict[rtl_name].add_cop(int(nodeid))
                rop_dict[rtl_name].add_line_num(int(node.line_num))
                rop_dict[rtl_name].add_latency(int(node.latency))

                cop_dict[nodeid] = c_operator(node.nodeid, node.name, rop_dict[rtl_name].rtl_id, rtl_name, optype,
                                              node.opcode, node.line_num, node.c_step,
                                              node.latency, node.instruction, node.opnd_num, node.bw_out, node.bw_0,
                                              node.bw_1, node.bw_2, node.m_delay)
            else:
                rop_dict[rtl_name] = rtl_operator(rtl_name, rtl_id, node.bw_out, node.opnd_num, node.bw_0, node.bw_1,
                                                  node.bw_2,
                                                  optype, node.opcode, node.m_delay)
                rop_dict[rtl_name].add_cop(int(nodeid))
                rop_dict[rtl_name].add_line_num(int(node.line_num))
                rop_dict[rtl_name].add_latency(int(node.latency))
                cop_dict[nodeid] = c_operator(node.nodeid, node.name, rtl_id, rtl_name, optype, node.opcode,
                                              node.line_num, node.c_step,
                                              node.latency, node.instruction, node.opnd_num, node.bw_out, node.bw_0,
                                              node.bw_1, node.bw_2, node.m_delay)
                rtl_id = rtl_id + 1
    return rtl_id


def get_rtlop_reg_name(IRinfo, cdfg_fsm_node_dict, rop_dict):
    for dp_regname_nodes in IRinfo.iter('dp_regname_nodes'):
        for regitem in dp_regname_nodes.findall('item'):
            real_name = regitem.find('first').text
            for regnode in regitem.find('second').findall('item'):
                nodeid = int(regnode.text)
                if nodeid in cdfg_fsm_node_dict:
                    node = cdfg_fsm_node_dict[nodeid]
                    if (node.rtl_name in rop_dict) and (real_name not in rop_dict[node.rtl_name].reg_name):
                        rop_dict[node.rtl_name].add_reg_name(real_name)


def get_rtlop_comp_name(IRinfo, rop_dict):
    for dp_fu_nodes_expression in IRinfo.iter('dp_fu_nodes_expression'):
        for fu_node in dp_fu_nodes_expression.findall('item'):
            comp_name = fu_node.find('first').text
            comp_node_set = set()
            for node_item in fu_node.find('second').findall('item'):
                comp_node_set.add(int(node_item.text))
            for name in rop_dict:
                if len(rop_dict[name].cop_set - comp_node_set) == 0:
                    rop_dict[name].comp_name = comp_name

    for dp_fu_nodes_expression in IRinfo.iter('dp_fu_nodes_module'):
        for fu_node in dp_fu_nodes_expression.findall('item'):
            comp_name = fu_node.find('first').text
            comp_node_set = set()
            for node_item in fu_node.find('second').findall('item'):
                comp_node_set.add(int(node_item.text))
            for name in rop_dict:
                if len(rop_dict[name].cop_set - comp_node_set) == 0:
                    rop_dict[name].comp_name = comp_name


def instruction_revise(src_path, kernel, cdfg_fsm_node_dict):
    with open('{}/{}.txt'.format(src_path, kernel), 'r') as rfile:
        inst_list = rfile.readlines()
    ismatch = dict()
    for instruction in inst_list:
        ismatch[instruction] = 0
    for nodeid in cdfg_fsm_node_dict:
        if cdfg_fsm_node_dict[nodeid].opcode == 'store':
            name = re.split(' ', cdfg_fsm_node_dict[nodeid].instruction.strip(''))[6]
            name2 = re.split(' ', cdfg_fsm_node_dict[nodeid].instruction.strip(''))[4].strip(',')
            for instruction in inst_list:
                if re.match('  store', instruction) and ismatch[instruction] == 0:
                    tmp = re.split(' ', instruction)[6]
                    tmp2 = re.split(' ', instruction)[4]
                    if re.match(name, tmp) and re.match(name2, tmp2):
                        if instruction.find('!') != -1:
                            instruction = re.split(', !', instruction)[0]
                        cdfg_fsm_node_dict[nodeid].instruction = instruction.strip('\n')
                        ismatch[instruction] = 1
                        break

        elif cdfg_fsm_node_dict[nodeid].opcode == 'write':
            name = re.split(' ', cdfg_fsm_node_dict[nodeid].instruction.strip(''))[6].strip(',')
            name2 = re.split(' ', cdfg_fsm_node_dict[nodeid].instruction.strip(''))[8]
            for instruction in inst_list:
                if re.match('  call void @_ssdm_op_Write', instruction) and ismatch[instruction] == 0:
                    tmp = re.split(' ', instruction.strip(' '))[3].strip(',')
                    tmp2 = re.split(' ', instruction.strip(' '))[5]
                    if re.match(name, tmp) and re.match(name2, tmp2):
                        if instruction.find('!') != -1:
                            instruction = re.split(', !', instruction)[0]
                        cdfg_fsm_node_dict[nodeid].instruction = instruction.strip('\n')
                        ismatch[instruction] = 1
                        break
        else:
            name = '  %' + cdfg_fsm_node_dict[nodeid].name + ' '
            for instruction in inst_list:
                if re.match(name, instruction):
                    if instruction.find('!') != -1:
                        instruction = re.split(', !', instruction)[0]
                    cdfg_fsm_node_dict[nodeid].instruction = instruction.strip('\n')
                    break


def c_rtl_op_explore(info_dir, IRinfo, cdfg_fsm_node_dict, rsc_dict, kernel_name, rtl_id, nodeid_max):
    cop_dict = dict()
    rop_dict = dict()
    rtl_id = get_arith_logic_arbit_op(cdfg_fsm_node_dict, rsc_dict, cop_dict, rop_dict, rtl_id)
    rtl_id = get_mem_op(IRinfo, cdfg_fsm_node_dict, rsc_dict, cop_dict, rop_dict, rtl_id, nodeid_max)

    get_rtlop_reg_name(IRinfo, cdfg_fsm_node_dict, rop_dict)
    get_rtlop_comp_name(IRinfo, rop_dict)

    with open('{}/{}/rop_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        title = ['rtl_name', 'comp_name', 'rtl_id', 'optype', 'opcode', 'reg_name', 'opnd_num', 'bw_out', 'bw_0',
                 'bw_1', 'bw_2', 'lut', 'dsp', 'bram', 'ff',
                 'cop_set', 'line_num_set', 'latency_set', 'latency', 'delay']
        writer.writerow(title)
        for name in rop_dict:
            rop = rop_dict[name]
            wr_line = [rop.rtl_name, rop.comp_name, rop.rtl_id, rop.optype, rop.opcode,
                       '{}'.format(', '.join(map(str, rop.reg_name))), rop.opnd_num, rop.bw_out,
                       rop.bw_0, rop.bw_1, rop.bw_2, rop.lut, rop.dsp, rop.bram, rop.ff,
                       str(sorted(rop.cop_set)).strip('[]'), str(sorted(rop.line_num_set)).strip('[]'),
                       str(sorted(rop.latency_set)).strip('[]'),
                       rop.latency, rop.delay]
            writer.writerow(wr_line)

    with open('{}/{}/cop_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        title = ['nodeid', 'name', 'rtl_id', 'rtl_name', 'optype', 'opcode', 'line_num', 'c_step', 'latency',
                 'opnd_num', 'bw_out', 'bw_0', 'bw_1', 'bw_2',
                 'm_delay', 'instruction']
        writer.writerow(title)
        for nodeid in cop_dict:
            cop = cop_dict[nodeid]
            if cop.rtl_name == 'not_exist':
                print('CHECK: cop ({}) in cop_dict does not has rtl_name'.format(nodeid))
            wr_line = [cop.nodeid, cop.name, cop.rtl_id, cop.rtl_name, cop.optype, cop.opcode, cop.line_num, cop.c_step,
                       cop.latency, cop.opnd_num, cop.bw_out, cop.bw_0,
                       cop.bw_1, cop.bw_2, cop.m_delay, cop.instruction]
            writer.writerow(wr_line)

    # with open('{}/cop_dict.txt'.format(info_dir), 'w+', newline = '') as wfile:
    #     for nodeid in cop_dict:
    #         cop = cop_dict[nodeid]
    #         wr_line = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(cop.nodeid, cop.name, cop.rtl_id, cop.rtl_id, cop.rtl_name, cop.optype, 
    #             cop.opcode, cop.c_step, cop.latency, cop.opnd_num, cop.bw_out, cop.bw_0, cop.bw_1, cop.bw_2, cop.m_delay, cop.instruction)
    #         wfile.write(wr_line + "\n")

    return cop_dict, rop_dict, rtl_id


###################################################################
def get_global_info(RSCinfo):
    global_dict = dict()
    for section in RSCinfo.findall('section'):
        if section.get('name') == 'Performance Estimates':
            for item in section.findall('item'):
                if item.get('name') == 'Timing':
                    for column in item.iter('column'):
                        if column.get('name') == 'ap_clk':
                            timing_list = column.text.split(', ')
                            global_dict['clk_target'] = float(timing_list[0].strip('ns'))
                            global_dict['clk_estimated'] = float(timing_list[1].strip('ns'))
                            global_dict['clk_uncertainty'] = float(timing_list[2].strip('ns'))

                elif item.get('name') == 'Latency':
                    for column in item.iter('column'):
                        if column.get('name') == '':
                            latency_list = column.text.replace('?', '1000').split(', ')
                            global_dict['latency_min'] = int(latency_list[0])
                            global_dict['latency_max'] = int(latency_list[1])
                            global_dict['interval_min'] = int(latency_list[4])
                            global_dict['interval_max'] = int(latency_list[5])

        elif section.get('name') == 'Utilization Estimates':
            global_dict['bram'] = 0
            global_dict['dsp'] = 0
            global_dict['ff'] = 0
            global_dict['lut'] = 0
            global_dict['uram'] = 0
            for item in section.findall('item'):
                if item.get('name') == 'Summary':
                    for column in item.iter('column'):
                        res_list = column.text.split(', ')
                        if not res_list[0] == '-':
                            global_dict['bram'] += int(res_list[0])
                        if not res_list[1] == '-':
                            global_dict['dsp'] += int(res_list[1])
                        if not res_list[2] == '-':
                            global_dict['ff'] += int(res_list[2])
                        if not res_list[3] == '-':
                            global_dict['lut'] += int(res_list[3])
                        if not res_list[4] == '-':
                            global_dict['uram'] += int(res_list[4])
                    break
    return global_dict


def global_explore(info_dir, RSCinfo, kernel_name):
    global_dict = get_global_info(RSCinfo)
    with open('{}/final/global_dict.csv'.format(info_dir), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        for name in global_dict:
            val = global_dict[name]
            wr_line = [name, val]
            writer.writerow(wr_line)
    return global_dict


###################################################################
def set_graph_node_info(DG, nodeid, **kwargs):
    graph_node = DG.nodes[nodeid]
    for attr_name in kwargs:
        graph_node[attr_name] = kwargs[attr_name]


###########################
# compute the rop fanin/fanout before bypassing op and adding mux, not the very precise one in the RTL,
# but can use as a reference
def fan_in_out_compute(DG):
    for nodeid in DG.nodes:
        DG.nodes[nodeid]['fan_in'] = len(list(DG.predecessors(nodeid)))
        DG.nodes[nodeid]['fan_out'] = len(list(DG.successors(nodeid)))


###########################
# construct the graph: connects nodes and edges of fsm_node_dict; the edges use reg_flow
# = (from_reg, to_reg) to represent the dataflow with registers
def df_node_edge_construct(DG, fsm_node_dict, cdfg_fsm_node_dict, df_reg_dict, cop_dict):
    for nodeid in fsm_node_dict:
        fsm_node = fsm_node_dict[nodeid]
        DG.add_node(nodeid)
        if nodeid in cdfg_fsm_node_dict:
            opcode = cdfg_fsm_node_dict[nodeid].opcode
        else:
            opcode = 'not_exist'
        if nodeid in cop_dict:
            optype = cop_dict[nodeid].optype
        else:
            optype = 'not_exist'
        set_graph_node_info(DG, nodeid, node_id=nodeid, opid=fsm_node.opid, c_step=fsm_node.c_step,
                            stage=fsm_node.stage, opcode=opcode, optype=optype,
                            latency=fsm_node.latency, opnd_num=fsm_node.opnd_num, bw_out=fsm_node.bw_out,
                            bw_0=fsm_node.bw_0, bw_1=fsm_node.bw_1,
                            bw_2=fsm_node.bw_2, from_node_set=fsm_node.from_node_set, to_node_set=fsm_node.to_node_set,
                            instruction=fsm_node.instruction)

    for nodeid in fsm_node_dict:
        fsm_node = fsm_node_dict[nodeid]
        for from_nodeid in fsm_node.from_node_set:
            if from_nodeid in DG.nodes:
                DG.add_edge(from_nodeid, nodeid, reg_flow=[df_reg_dict[from_nodeid][nodeid]])
            else:
                print('CHECK: df_node_edge_construct: from_nodeid = {} not in DG'.format(from_nodeid))
                assert 0
        for to_nodeid in fsm_node.to_node_set:
            if to_nodeid in DG.nodes:
                DG.add_edge(nodeid, to_nodeid, reg_flow=[df_reg_dict[nodeid][to_nodeid]])
            else:
                print('CHECK: df_node_edge_construct: to_nodeid = {} not in DG'.format(to_nodeid))
                assert 0

    DG.remove_nodes_from(list(nx.isolates(DG)))


###########################
# graph trimming: remove trivial nodes in order to highlight arithmetic-intensive nodes and paths
df_bypass_op = ['const', 'br', 'bitconcatenate', 'zext', 'not_exist', 'partselect', 'reg',
                'bitcast', 'bitselect', 'trunc', 'switch', 'sext', 'urem', 'partset', 'extractvalue', 'call', 'dcmp']


def df_op_bypass(DG, df_bypass_op):
    for bypass_opcode in df_bypass_op:
        rm_node_list = list()
        for nodeid in DG.nodes:
            if DG.nodes[nodeid]['opcode'] == bypass_opcode:
                for pre_id in list(DG.predecessors(nodeid)):
                    for suc_id in list(DG.successors(nodeid)):
                        # check the correctness of reg_flow connection: from_reg1->to_reg1/from_reg2->to_reg2,
                        # to_reg1 = from_reg2
                        if DG[pre_id][nodeid]['reg_flow'][0][1] != DG[nodeid][suc_id]['reg_flow'][0][0]:
                            print(
                                'CHECK: df_op_bypass: reg_flow correspondence not match: {} != {} for '
                                'connecting id: {} -> {} -> {}'.format(
                                    DG[pre_id][nodeid]['reg_flow'][0][1], DG[nodeid][suc_id]['reg_flow'][0][0], pre_id,
                                    nodeid, suc_id))
                            assert 0

                        reg_flow = [(DG[pre_id][nodeid]['reg_flow'][0][0], DG[nodeid][suc_id]['reg_flow'][0][1],
                                     DG[pre_id][nodeid]['reg_flow'][0][2], DG[nodeid][suc_id]['reg_flow'][0][3])]
                        if DG.has_edge(pre_id, suc_id):
                            DG[pre_id][suc_id]['reg_flow'] = list(set(DG[pre_id][suc_id]['reg_flow'] + reg_flow))
                        else:
                            DG.add_edge(pre_id, suc_id, reg_flow=reg_flow)
                rm_node_list.append(nodeid)
        DG.remove_nodes_from(rm_node_list)


###########################
# node merging: connect all edges of nodeid2 to nodeid1, then delete nodeid2
# if there exists the same edges (reg_flow the same) before merging, merge reg_flow; otherwise copy reg_flow
def contracted_nodes(DG, nodeid1, nodeid2):
    if nodeid1 in DG.nodes and nodeid2 in DG.nodes:
        for pre_id in list(DG.predecessors(nodeid2)):
            if DG.has_edge(pre_id, nodeid1):
                DG[pre_id][nodeid1]['reg_flow'] = list(
                    set(DG[pre_id][nodeid1]['reg_flow'] + DG[pre_id][nodeid2]['reg_flow']))
            else:
                DG.add_edge(pre_id, nodeid1, reg_flow=list(set(DG[pre_id][nodeid2]['reg_flow'])))

        for suc_id in list(DG.successors(nodeid2)):
            if DG.has_edge(nodeid1, suc_id):
                DG[nodeid1][suc_id]['reg_flow'] = list(
                    set(DG[nodeid1][suc_id]['reg_flow'] + DG[nodeid2][suc_id]['reg_flow']))
            else:
                DG.add_edge(nodeid1, suc_id, reg_flow=list(set(DG[nodeid2][suc_id]['reg_flow'])))
        DG.remove_node(nodeid2)
    else:
        print('CHECK: contracted_nodes: nodeid1 = {} or nodeid2 = {} not exist in DG.nodes'.format(nodeid1, nodeid2))
        assert 0


# compute the locations of item in seq, return a list of locations (allow returning multiple locations)
def duplicate_extract(seq, item):
    start_at = -1
    locs = []
    while True:
        try:
            loc = seq.index(item, start_at + 1)
        except ValueError:
            break
        else:
            locs.append(loc)
            start_at = loc
    return locs


# merge all cop of the same rtlop; pay attention: load/store are not completely merged so that
# the reg_flow can be clearly represented
# separately deal with load/store: check whether the connection are identical: pre_op -> load/store -> suc_op
# merge if connected to the same pre_op and suc_op, and then denote this relationship in the edge:
# multiple reg_flow in the same edge
def df_node_merge(DG, rop_dict):
    for rtl_name in rop_dict:
        rop = rop_dict[rtl_name]
        cop_list = sorted(list(rop.cop_set))

        if rop.optype in ['memory', 'io']:
            if rop.opcode == 'write':
                continue
            load_list = [cop for cop in cop_list if DG.nodes[cop]['opcode'] == 'load']
            store_list = [cop for cop in cop_list if DG.nodes[cop]['opcode'] == 'store']
            for i, target_list in enumerate([load_list, store_list]):
                if len(target_list) == 0:
                    continue
                neighbor_list = list()
                duplicate_list = list()
                for nodeid in target_list:
                    pre_list = list(DG.predecessors(nodeid))
                    suc_list = list(DG.successors(nodeid))
                    neighbor_list.append((pre_list, suc_list))
                for neighbor in neighbor_list:
                    duplicates = duplicate_extract(neighbor_list, neighbor)
                    if duplicates not in duplicate_list and len(duplicates) > 1:
                        duplicate_list.append(duplicates)
                for duplicates in duplicate_list:
                    node_list = list(itemgetter(*duplicates)(target_list))
                    for nodeid in node_list[1:]:
                        contracted_nodes(DG, node_list[0], nodeid)
                    set_graph_node_info(DG, node_list[0], node_id=node_list[0], merge_op_set=node_list)

        elif len(cop_list) > 1:  # rop.optype not in ['memory', 'io']:
            if rop.opcode in df_bypass_op:
                continue
            if cop_list[0] not in DG.nodes:
                print('CHECK: df_node_merge: cop_list[0] = {} not in DG.nodes'.format(cop_list[0]))
                assert 0
            for nodeid in cop_list[1:]:
                if nodeid in DG.nodes:
                    contracted_nodes(DG, cop_list[0], nodeid)
                else:
                    print('CHECK: df_node_merge: nodeid = {} not in DG.nodes'.format(nodeid))
                    assert 0
            set_graph_node_info(DG, cop_list[0], node_id=cop_list[0], merge_op_set=cop_list)


###########################


###########################
# complement rtl info of nodes 
def df_rtl_info_add(DG, cdfg_fsm_node_dict, rop_dict):
    for nodeid in DG.nodes:
        if nodeid in cdfg_fsm_node_dict:
            cdfg_fsm_node = cdfg_fsm_node_dict[nodeid]
            if cdfg_fsm_node.rtl_name in rop_dict:
                rop_node = rop_dict[cdfg_fsm_node.rtl_name]
                set_graph_node_info(DG, nodeid, node_id=nodeid, rtl_name=rop_node.rtl_name, rtl_id=rop_node.rtl_id,
                                    reg_name=rop_node.reg_name,
                                    opnd_num=rop_node.opnd_num, bw_out=rop_node.bw_out, bw_0=rop_node.bw_0,
                                    bw_1=rop_node.bw_1, bw_2=rop_node.bw_2,
                                    lut=rop_node.lut, dsp=rop_node.dsp, bram=rop_node.bram, ff=rop_node.ff,
                                    optype=rop_node.optype, cop_set=rop_node.cop_set,
                                    line_num_set=rop_node.line_num_set,
                                    latency_set=rop_node.latency_set, latency=rop_node.latency, delay=rop_node.delay)


###########################
def is_str_int(str_in):
    try:
        int(str_in)
        return 1
    except ValueError:
        return 0


# extract node activities
def df_node_tracer_gen(DG, info_dir, cdfg_fsm_node_dict, cop_dict, rop_dict, kernel_name):
    cop_node_dict = defaultdict(set)
    for nodeid in DG.nodes:
        node_id = DG.nodes[nodeid]['node_id']
        if 'rtl_name' in DG.nodes[nodeid]:
            rtl_name = DG.nodes[nodeid]['rtl_name']
            rtl_op_set = rop_dict[rtl_name].cop_set
            for op_id in rtl_op_set:
                cop_node_dict[op_id].add(nodeid)

        if 'merge_op_set' in DG.nodes[nodeid]:
            merge_op_set = DG.nodes[nodeid]['merge_op_set']
            for op_id in merge_op_set:
                cop_node_dict[op_id].add(nodeid)

        if is_str_int(node_id):
            cop_node_dict[node_id].add(nodeid)

    with open('{}/{}/cop_node_dict.txt'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        for cop_id in cop_node_dict:
            if cop_id not in cop_dict:
                if cop_id in cdfg_fsm_node_dict:
                    if cdfg_fsm_node_dict[cop_id].opcode in ['phi', 'alloca', 'getelementptr']:
                        continue
                    cop = cdfg_fsm_node_dict[cop_id]
                    rtl_id = -1
                    rtl_name = 'not_exist'
                    optype = cop.opcode
                else:
                    continue
            else:
                cop = cop_dict[cop_id]
                rtl_name = cop.rtl_name
                rtl_id = cop.rtl_id
                optype = cop.optype

            node_id_list = str(list(cop_node_dict[cop_id])).strip('[').strip(']')
            wr_line = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(cop.nodeid, cop.name, node_id_list,
                                                                               rtl_id, rtl_name, optype,
                                                                               cop.opcode, cop.c_step, cop.latency,
                                                                               cop.opnd_num, cop.bw_out, cop.bw_0,
                                                                               cop.bw_1, cop.bw_2, cop.m_delay,
                                                                               cop.instruction.strip('\n'))
            wfile.write(wr_line + '\n')


###########################
class edge_obj:
    def __init__(self, edge_id, edge_src_id, edge_dst_id, src_id, dst_id, latency, cop_set=None):
        self.edge_id = edge_id
        self.edge_src_id = edge_src_id
        self.edge_dst_id = edge_dst_id
        self.src_id = src_id
        self.dst_id = dst_id
        self.latency = latency
        self.cop_set = set()
        if cop_set is not None:
            self.add_cop(cop_set)

    def add_cop(self, cop_id):
        cop_id_list = [cop_id] if type(cop_id) == int else cop_id
        self.cop_set = set(list(self.cop_set) + cop_id_list)


# generate the file required by the IR tracer
# to find the edge acitivity in graph act annotate: edge_id | src_node_id | dst_node_id | cop_set (for cop)
# to add tracer for cop in IR: cop_id | edge_id_list | opcode | opnd_num | bw_out | bw_0 | bw_1 | bw_2 | instruction
# the same cop can appear in different edge_id because of the merging process above
def df_edge_tracer_gen(DG, info_dir, cdfg_fsm_node_dict, cop_dict, rop_dict, kernel_name):
    cop_edge_dict = defaultdict(list)
    edge_obj_dict = dict()
    for edge_id, (src_id, dst_id) in enumerate(DG.edges):
        edge_src_id = 2 * edge_id
        edge_dst_id = 2 * edge_id + 1
        DG[src_id][dst_id]['edge_id'] = edge_id
        DG[src_id][dst_id]['edge_src_id'] = edge_src_id
        DG[src_id][dst_id]['edge_dst_id'] = edge_dst_id

        # if id not found, it is phi/io_mem/internal_mem, should be bypassed later
        src_cop_list = [reg_flow[2] for reg_flow in DG[src_id][dst_id]['reg_flow']]
        for nodeid in src_cop_list:
            cop_edge_dict[nodeid].append(edge_src_id)
            if nodeid in cdfg_fsm_node_dict:
                latency = cdfg_fsm_node_dict[nodeid].latency
            else:
                latency = 0

        edge_obj_dict[edge_src_id] = edge_obj(edge_id=edge_src_id, edge_src_id=edge_src_id, edge_dst_id=edge_dst_id,
                                              src_id=src_id, dst_id=dst_id, latency=latency, cop_set=src_cop_list)

        dst_cop_list = [reg_flow[3] for reg_flow in DG[src_id][dst_id]['reg_flow']]
        for nodeid in dst_cop_list:
            cop_edge_dict[nodeid].append(edge_dst_id)
            if nodeid in cdfg_fsm_node_dict:
                latency = cdfg_fsm_node_dict[nodeid].latency
            else:
                latency = 0

        edge_obj_dict[edge_dst_id] = edge_obj(edge_id=edge_dst_id, edge_src_id=edge_src_id, edge_dst_id=edge_dst_id,
                                              src_id=src_id, dst_id=dst_id, latency=latency, cop_set=dst_cop_list)

    with open('{}/{}/cop_edge_dict.txt'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        for cop_id in cop_edge_dict:
            if cop_id not in cop_dict:
                if cop_id in cdfg_fsm_node_dict:
                    if cdfg_fsm_node_dict[cop_id].opcode in ['phi', 'alloca', 'getelementptr']:
                        continue
                    cop = cdfg_fsm_node_dict[cop_id]
                    rtl_id = -1
                    rtl_name = 'not_exist'
                    optype = cop.opcode
                else:
                    continue
            else:
                cop = cop_dict[cop_id]
                rtl_name = cop.rtl_name
                rtl_id = cop.rtl_id
                optype = cop.optype

            edge_id_list = str(list(set(cop_edge_dict[cop_id]))).strip('[').strip(']')
            wr_line = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(cop.nodeid, cop.name, edge_id_list,
                                                                               rtl_id, rtl_name, optype,
                                                                               cop.opcode, cop.c_step, cop.latency,
                                                                               cop.opnd_num, cop.bw_out, cop.bw_0,
                                                                               cop.bw_1, cop.bw_2, cop.m_delay,
                                                                               cop.instruction.strip('\n'))
            wfile.write(wr_line + '\n')

    with open('{}/{}/edge_obj_dict.csv'.format(info_dir, kernel_name), 'w+', newline='') as wfile:
        writer = csv.writer(wfile)
        writer.writerow(['edge_id', 'edge_src_id', 'edge_dst_id', 'src_id', 'dst_id', 'latency', 'cop_set'])
        for edge_id in edge_obj_dict:
            edge_src_id = edge_obj_dict[edge_id].edge_src_id
            edge_dst_id = edge_obj_dict[edge_id].edge_dst_id
            src_id = edge_obj_dict[edge_id].src_id
            dst_id = edge_obj_dict[edge_id].dst_id
            latency = edge_obj_dict[edge_id].latency
            cop_set = str(edge_obj_dict[edge_id].cop_set).strip('{').strip('}')
            writer.writerow([edge_id, edge_src_id, edge_dst_id, src_id, dst_id, latency, cop_set])


def df_cc_trim(DG):
    rm_node_list = list()
    for subG in nx.weakly_connected_components(DG):
        find_critical_component = False
        for nodeid in subG:

            if nodeid == '\\n':
                continue
            if DG.nodes[nodeid]['opcode'] in ['dadd', 'dmul', 'ddiv', 'add', 'or', 'and', 'mul', 'fadd', 'fsub', 'fdiv',
                                              'read', 'write', 'load', 'store']:
                find_critical_component = True
                break
        if not find_critical_component:
            rm_node_list += list(subG)
    DG.remove_nodes_from(rm_node_list)


def df_graph_visualize2(out_dir, save_name, act_plot=False):
    DG = nx.DiGraph(nx.drawing.nx_pydot.read_dot('{}/{}.dot'.format(out_dir, save_name)))
    gvz_graph = gvz.Digraph(format='png', filename='{}/{}'.format(out_dir, save_name))
    gvz_graph.attr('node', fontsize='50')
    gvz_graph.attr('edge', arrowsize='2.4', fontsize='30')
    for nodeid in DG.nodes:
        if nodeid == '\\n':
            continue
        if DG.nodes[nodeid]['opcode'] in ['internal_mem', 'io_mem', 'io_port_in', 'io_port_out']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='1')
        elif DG.nodes[nodeid]['opcode'] in ['fadd', 'fsub', 'fmul', 'fdiv', 'dadd', 'dmul', 'dsub', 'ddiv', 'add',
                                            'sub', 'mul']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='2')
        elif DG.nodes[nodeid]['opcode'] in ['store']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='4')
        elif DG.nodes[nodeid]['opcode'] in ['and', 'or', 'xor', 'icmp', 'shl', 'lshr']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='5')
        elif DG.nodes[nodeid]['opcode'] in ['phi', 'mux', 'select']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='8')
        elif DG.nodes[nodeid]['opcode'] in ['load']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='6')
        else:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='3')

        if DG.nodes[nodeid]['opcode'] in ['internal_mem', 'io_mem', 'io_port_in', 'io_port_out']:
            gvz_graph.node(str(nodeid), label='{} - {}\n{}'.format(DG.nodes[nodeid]['node_id'], nodeid,
                                                                   DG.nodes[nodeid]['rtl_name']))
        else:
            gvz_graph.node(str(nodeid),
                           label='{} - {} \n{}'.format(DG.nodes[nodeid]['node_id'], nodeid, DG.nodes[nodeid]['opcode']))

    for edge in DG.edges:
        if act_plot:
            gvz_graph.edge(str(edge[0]), str(edge[1]),
                           label='{}-{}\n{:.4f}/{:.4f}\n{:.4f}/{:.4f}'.format(DG[edge[0]][edge[1]]['edge_src_id'],
                                                                              DG[edge[0]][edge[1]]['edge_dst_id'],
                                                                              float(DG[edge[0]][edge[1]][
                                                                                        'src_activity'].strip('\"')),
                                                                              float(DG[edge[0]][edge[1]][
                                                                                        'dst_activity'].strip('\"')),
                                                                              float(DG[edge[0]][edge[1]][
                                                                                        'src_act_ratio'].strip('\"')),
                                                                              float(DG[edge[0]][edge[1]][
                                                                                        'dst_act_ratio'].strip('\"'))))
        else:
            gvz_graph.edge(str(edge[0]), str(edge[1]), label='{}-{}'.format(DG[edge[0]][edge[1]]['edge_src_id'],
                                                                            DG[edge[0]][edge[1]]['edge_dst_id']))
    try:
        gvz_graph.render(view=False)
    except:
        print("CHECK: df_graph_visualize: draw error")


###########################
def df_graph_visualize(out_dir, kernel_name, save_name, act_plot=False):
    DG = nx.DiGraph(nx.drawing.nx_pydot.read_dot('{}/{}/{}.dot'.format(out_dir, kernel_name, save_name)))
    gvz_graph = gvz.Digraph(format='png', filename='{}/{}/{}'.format(out_dir, kernel_name, save_name))
    gvz_graph.attr('node', fontsize='50')
    gvz_graph.attr('edge', arrowsize='2.4', fontsize='30')
    for nodeid in DG.nodes:
        if nodeid == '\\n':
            continue
        if DG.nodes[nodeid]['opcode'] in ['internal_mem', 'io_mem', 'io_port_in', 'io_port_out']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='1')
        elif DG.nodes[nodeid]['opcode'] in ['fadd', 'fsub', 'fmul', 'fdiv', 'dadd', 'dmul', 'dsub', 'ddiv', 'add',
                                            'sub', 'mul']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='2')
        elif DG.nodes[nodeid]['opcode'] in ['store']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='4')
        elif DG.nodes[nodeid]['opcode'] in ['and', 'or', 'xor', 'icmp', 'shl', 'lshr']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='5')
        elif DG.nodes[nodeid]['opcode'] in ['phi', 'mux', 'select']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='8')
        elif DG.nodes[nodeid]['opcode'] in ['load']:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='6')
        else:
            gvz_graph.attr('node', style='filled', colorscheme='set28', color='3')

        if DG.nodes[nodeid]['opcode'] in ['internal_mem', 'io_mem', 'io_port_in', 'io_port_out']:
            gvz_graph.node(str(nodeid), label='{} - {}\n{}'.format(DG.nodes[nodeid]['node_id'], nodeid,
                                                                   DG.nodes[nodeid]['rtl_name']))
        else:
            gvz_graph.node(str(nodeid),
                           label='{} - {} \n{}'.format(DG.nodes[nodeid]['node_id'], nodeid, DG.nodes[nodeid]['opcode']))

    for edge in DG.edges:
        if act_plot:
            gvz_graph.edge(str(edge[0]), str(edge[1]),
                           label='{}-{}\n{:.4f}/{:.4f}\n{:.4f}/{:.4f}'.format(DG[edge[0]][edge[1]]['edge_src_id'],
                                                                              DG[edge[0]][edge[1]]['edge_dst_id'],
                                                                              float(DG[edge[0]][edge[1]][
                                                                                        'src_activity'].strip('\"')),
                                                                              float(DG[edge[0]][edge[1]][
                                                                                        'dst_activity'].strip('\"')),
                                                                              float(DG[edge[0]][edge[1]][
                                                                                        'src_act_ratio'].strip('\"')),
                                                                              float(DG[edge[0]][edge[1]][
                                                                                        'dst_act_ratio'].strip('\"'))))
        else:
            gvz_graph.edge(str(edge[0]), str(edge[1]), label='{}-{}'.format(DG[edge[0]][edge[1]]['edge_src_id'],
                                                                            DG[edge[0]][edge[1]]['edge_dst_id']))
    try:
        gvz_graph.render(view=False)
    except:
        print("CHECK: df_graph_visualize: draw error")


###################################################################
def graph_visualize(out_dir, save_name, rop_name_dict, act_plot=False):
    DG = nx.DiGraph(nx.drawing.nx_pydot.read_dot('{}/{}.dot'.format(out_dir, save_name)))
    gvz_list = [gvz.Digraph(format='png', filename='{}/{}_opcode'.format(out_dir, save_name)),
                gvz.Digraph(format='png', filename='{}/{}_rtlop'.format(out_dir, save_name))]

    for color_scheme, gvz_graph in enumerate(gvz_list):
        gvz_graph.attr('node', fontsize='50')
        gvz_graph.attr('edge', arrowsize='2.4', fontsize='30')
        for nodeid in DG.nodes:
            if color_scheme == 0:  # color scheme 1: coloring different node opcode ###
                if DG.nodes[nodeid]['comp_type'] in ['fadd', 'fmul']:
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='2')
                elif DG.nodes[nodeid]['comp_type'] in ['io_mem', 'write', 'internal_mem']:
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='1')
                elif DG.nodes[nodeid]['comp_type'] in ['reg', 'icmp', 'or']:
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='3')
                elif DG.nodes[nodeid]['comp_type'] in ['mux', 'select']:
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='4')
                elif DG.nodes[nodeid]['comp_type'] in ['add', 'mul']:
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='6')
                elif DG.nodes[nodeid]['comp_type'] in ['load', 'store']:
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='5')
                else:
                    gvz_graph.attr('node', style='', colorscheme='set28', color='8')
            elif color_scheme == 1:  # color scheme 2: emphasizing rtl node ###
                if 'comp_name' in DG.nodes[nodeid]:
                    if DG.nodes[nodeid]['rtl_name'] in rop_name_dict:
                        gvz_graph.attr('node', style='filled', colorscheme='set28', color='2')
                    else:
                        gvz_graph.attr('node', style='filled', colorscheme='set28', color='3')
                elif 'opcode' in DG.nodes[nodeid]:
                    if DG.nodes[nodeid]['opcode'] == 'const':
                        gvz_graph.attr('node', style='filled', colorscheme='set28', color='1')
                    else:
                        gvz_graph.attr('node', style='filled', colorscheme='set28', color='3')
                else:
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='3')

            if DG.nodes[nodeid]['comp_type'] in ['io_mem']:
                gvz_graph.node(str(nodeid),
                               label='{}\n{}'.format(DG.nodes[nodeid]['compid'], DG.nodes[nodeid]['comp_name']))
            elif DG.nodes[nodeid]['comp_type'] in ['internal_mem']:
                gvz_graph.node(str(nodeid),
                               label='{}\n{}'.format(DG.nodes[nodeid]['compid'], DG.nodes[nodeid]['rtl_name']))
            elif 'opcode' in DG.nodes[nodeid]:
                if DG.nodes[nodeid]['opcode'] == 'const':
                    gvz_graph.node(str(nodeid),
                                   label='{}\n{}'.format(DG.nodes[nodeid]['compid'], DG.nodes[nodeid]['opcode']))
                else:
                    gvz_graph.node(str(nodeid),
                                   label='{}\n{}'.format(DG.nodes[nodeid]['compid'], DG.nodes[nodeid]['comp_type']))
            else:
                gvz_graph.node(str(nodeid),
                               label='{}\n{}'.format(DG.nodes[nodeid]['compid'], DG.nodes[nodeid]['comp_type']))

        for edge in DG.edges:
            if act_plot:
                gvz_graph.edge(str(edge[0]), str(edge[1]),
                               label='{}\n{:.4f}'.format(DG[edge[0]][edge[1]]['pin_in_index'],
                                                         float(DG[edge[0]][edge[1]]['activity'].strip("\""))))
            else:
                gvz_graph.edge(str(edge[0]), str(edge[1]), label='{}'.format(DG[edge[0]][edge[1]]['pin_in_index']))

        gvz_graph.render(view=False)


###########################
def df_graph_construct(info_dir, fsm_node_dict, cdfg_fsm_node_dict, df_reg_dict, cop_dict, rop_dict, kernel_name):
    DG = nx.DiGraph()
    df_node_edge_construct(DG, fsm_node_dict, cdfg_fsm_node_dict, df_reg_dict, cop_dict)

    # df_op_bypass(DG, df_bypass_op)
    df_node_merge(DG, rop_dict)

    df_rtl_info_add(DG, cdfg_fsm_node_dict, rop_dict)
    # DG = nx.convert_node_labels_to_integers(DG)

    nx.nx_pydot.write_dot(DG, '{}/{}/DG.dot'.format(info_dir, kernel_name))

    return DG


def cdfg_fsm_node_dict_merge(dict1, dict2):
    for keys in dict2:
        if keys not in dict1:
            dict1[keys] = dict2[keys]
    return dict1


def cop_dict_merge(dict1, dict2):
    for keys in dict2:
        if keys not in dict1:
            dict1[keys] = dict2[keys]
    return dict1


def rop_dict_merge(dict1, dict2):
    for keys in dict2:
        if keys not in dict1:
            dict1[keys] = dict2[keys]
        else:
            dict1[keys].cop_set = dict1[keys].cop_set | dict2[keys].cop_set
            dict1[keys].line_num = dict1[keys].line_num_set | dict2[keys].line_num_set
            dict1[keys].latency_set = dict1[keys].latency_set | dict2[keys].latency_set
            dict1[keys].latency = sum(list(dict1[keys].latency_set)) / len(list(dict1[keys].latency_set))
    return dict1


###########################################################################################
def op_extract(info_dir, IR_file, FSMD_file, RSC_file, kernel_name, rtl_id, nodeid_max):
    IRinfo = ET.parse(IR_file).getroot()
    FSMDinfo = ET.parse(FSMD_file).getroot()
    RSCinfo = ET.parse(RSC_file).getroot()

    cdfg_node_dict, op_set = cdfg_node_explore(info_dir, IRinfo, kernel_name, nodeid_max)
    fsm_node_dict, op_node_mapping_dict = fsm_node_explore(info_dir, FSMDinfo, kernel_name, nodeid_max)
    cdfg_fsm_node_dict = cdfg_fsm_node_explore(info_dir, cdfg_node_dict, fsm_node_dict, kernel_name)
    instruction_revise(args.src_path, kernel_name, cdfg_fsm_node_dict)
    rsc_dict = sub_component_rsc_explore(info_dir, IRinfo, kernel_name)
    global_dict = global_explore(info_dir, RSCinfo, kernel_name)
    cop_dict, rop_dict, rtl_id = c_rtl_op_explore(info_dir, IRinfo, cdfg_fsm_node_dict, rsc_dict, kernel_name, rtl_id,
                                                  nodeid_max)
    df_reg_dict = get_df_reg(FSMDinfo, op_node_mapping_dict, cdfg_fsm_node_dict)

    DG = df_graph_construct(info_dir, fsm_node_dict, cdfg_fsm_node_dict, df_reg_dict, cop_dict, rop_dict, kernel_name)
    print('total number of rtl_operators: {}'.format(rtl_id))
    return DG, cdfg_fsm_node_dict, cop_dict, rop_dict, rtl_id


def sub_extract(info_dir, IR_file, FSMD_file, kernel_name, rtl_id, nodeid_max):
    IRinfo = ET.parse(IR_file).getroot()
    FSMDinfo = ET.parse(FSMD_file).getroot()

    cdfg_node_dict, op_set = cdfg_node_explore(info_dir, IRinfo, kernel_name, nodeid_max)
    fsm_node_dict, op_node_mapping_dict = fsm_node_explore(info_dir, FSMDinfo, kernel_name, nodeid_max)
    cdfg_fsm_node_dict = cdfg_fsm_node_explore(info_dir, cdfg_node_dict, fsm_node_dict, kernel_name)
    instruction_revise(args.src_path, kernel_name, cdfg_fsm_node_dict)
    rsc_dict = sub_component_rsc_explore(info_dir, IRinfo, kernel_name)

    cop_dict, rop_dict, rtl_id = c_rtl_op_explore(info_dir, IRinfo, cdfg_fsm_node_dict, rsc_dict, kernel_name, rtl_id,
                                                  nodeid_max)
    df_reg_dict = get_df_reg(FSMDinfo, op_node_mapping_dict, cdfg_fsm_node_dict)

    DG = df_graph_construct(info_dir, fsm_node_dict, cdfg_fsm_node_dict, df_reg_dict, cop_dict, rop_dict, kernel_name)
    print('total number of rtl_operators: {}'.format(rtl_id))
    return DG, cdfg_fsm_node_dict, cop_dict, rop_dict, rtl_id


###################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract c-operators and rtl-operators from HLS, construct cdfg graph',
                                     epilog='')
    parser.add_argument('kernel_name', help="input: kernel_name of HLS function")
    parser.add_argument('--src_path', required=True, help="directory path of input files", action='store')
    parser.add_argument('--dest_path', required=True, help="directory path of output files", action='store')
    rtl_id = 0
    nodeid_max = 0
    args = parser.parse_args()
    IR_file = '{}/{}.adb'.format(args.src_path, args.kernel_name)
    FSMD_file = '{}/{}.adb.xml'.format(args.src_path, args.kernel_name)
    RSC_file = '{}/{}.verbose.rpt.xml'.format(args.src_path, args.kernel_name)
    DG = nx.DiGraph
    os.system('mkdir {}/{}'.format(args.dest_path, args.kernel_name))
    os.system('mkdir {}/final'.format(args.dest_path))
    DG, main_node_dict, cop_dict, rop_dict, rtl_id = op_extract(args.dest_path, IR_file, FSMD_file, RSC_file,
                                                                args.kernel_name, rtl_id, nodeid_max)
    # Net_file = '{}/{}.verbose.rpt'.format(args.src_path, args.kernel_name)
    nodeid_max = get_nodeid_max(main_node_dict)
    for kernel_name in kernel_list:
        if os.path.exists('{}/{}.adb'.format(args.src_path, kernel_name)):
            IR_file = '{}/{}.adb'.format(args.src_path, kernel_name)
            FSMD_file = '{}/{}.adb.xml'.format(args.src_path, kernel_name)
        else:
            kernel_name2 = kernel_name.replace('.', '_')
            IR_file = '{}/{}.adb'.format(args.src_path, kernel_name2)
            FSMD_file = '{}/{}.adb.xml'.format(args.src_path, kernel_name2)
        os.system('mkdir {}/{}'.format(args.dest_path, kernel_name))
        sub_DG, sub_node_dict, sub_c_dict, sub_r_dict, rtl_id = sub_extract(args.dest_path, IR_file, FSMD_file,
                                                                            kernel_name, rtl_id, nodeid_max)
        main_node_dict = cdfg_fsm_node_dict_merge(main_node_dict, sub_node_dict)
        cop_dict = cop_dict_merge(cop_dict, sub_c_dict)
        rop_dict = rop_dict_merge(rop_dict, sub_r_dict)
        nodeid_max = get_nodeid_max(sub_node_dict)
        sub_list = list()
        main_list = list()
        main_dict = dict()
        sub_dict = dict()
        graph_dict = dict()
        ret_node = '0'
        main_node = '0'
        with open('{}/{}.txt'.format(args.src_path, args.kernel_name), 'r') as rfile:
            inst_list = rfile.readlines()
            for instruction in inst_list:

                if re.search('{}\('.format(kernel_name), instruction) and re.search('call', instruction):
                    main_call = re.split('\(|\)', instruction)[1]
                    main_list = re.split(', ', main_call)
        with open('{}/{}.txt'.format(args.src_path, kernel_name), 'r') as rfiles:
            inst_list = rfiles.readlines()
            for instruction in inst_list:
                if re.search('{}\('.format(kernel_name), instruction) and re.match('define internal', instruction):
                    sub_call = re.split('\(|\)', instruction)[1]
                    sub_list = re.split(', ', sub_call)
                if re.search('ret', instruction):
                    ret = re.split(' +|,', instruction)[3].strip('%')

                    for nodeid in sub_node_dict:
                        if sub_node_dict[nodeid].name == ret:
                            ret_node = nodeid

        for i in range(0, len(main_list)):
            main_list[i] = re.split(' |%', main_list[i])[1]
            sub_list[i] = re.split('%', sub_list[i])[1]

        for nodeid in main_node_dict:
            if main_node_dict[nodeid].opcode == 'call' and re.search('{}\('.format(kernel_name),
                                                                     main_node_dict[nodeid].instruction):
                retnode = list(main_node_dict[nodeid].to_node_set)
                if len(retnode):
                    main_node = retnode[0]
                node_list = list(main_node_dict[nodeid].from_node_set)
                for node in node_list:
                    for name in main_list:
                        if main_node_dict[node].name == name:
                            main_dict[name] = node
        for nodeid in sub_node_dict:
            if sub_node_dict[nodeid].opcode == 'read':

                name = re.split(' %|\)', sub_node_dict[nodeid].instruction)[2]
                for name2 in sub_list:
                    if name == name2:
                        sub_dict[name] = nodeid
        for i in range(0, len(main_list)):
            if main_list[i] in main_dict and sub_list[i] in sub_dict:
                graph_dict[main_dict[main_list[i]]] = sub_dict[sub_list[i]]
        H = nx.compose(DG, sub_DG)

        if ret_node != '0' and main_node != '0':
            H.add_edge(ret_node, main_node,
                       reg_flow=[(sub_node_dict[ret_node].name, main_node_dict[main_node].name, ret_node, main_node)])
        for nodeid in graph_dict:
            H.add_edge(nodeid, graph_dict[nodeid], reg_flow=[
                (main_node_dict[nodeid].name, sub_node_dict[graph_dict[nodeid]].name, nodeid, graph_dict[nodeid])])
        DG = H
    df_op_bypass(DG, df_bypass_op)
    call_list = list()
    for nodeid in DG.nodes:
        if DG.nodes[nodeid]['opcode'] == 'call':
            call_list.append(nodeid)
    DG.remove_nodes_from(call_list)
    DG = nx.convert_node_labels_to_integers(DG)
    for edge_id, (src_id, dst_id) in enumerate(DG.edges):
        edge_src_id = 2 * edge_id
        edge_dst_id = 2 * edge_id + 1
        DG[src_id][dst_id]['edge_id'] = edge_id
        DG[src_id][dst_id]['edge_src_id'] = edge_src_id
        DG[src_id][dst_id]['edge_dst_id'] = edge_dst_id
    nx.nx_pydot.write_dot(DG, '{}/final/DG.dot'.format(args.dest_path))
    df_node_tracer_gen(DG, args.dest_path, main_node_dict, cop_dict, rop_dict, 'final')
    df_edge_tracer_gen(DG, args.dest_path, main_node_dict, cop_dict, rop_dict, 'final')
    if DG.number_of_edges() < PLOT_EDGE_LIMIT:
        df_graph_visualize(args.dest_path, 'final', 'DG', act_plot=False)
