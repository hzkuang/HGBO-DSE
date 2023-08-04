import csv
import glob
import networkx as nx
import graphviz as gvz
import xml.etree.cElementTree as cET
import numpy as np
from sklearn.preprocessing import OneHotEncoder
import torch
from torch_geometric.data import Data


constFlag = 1  # whether extract const: 1/0
blockFlag = 1  # whether extract block: 1/0
plotFlag = 1  # whether draw cdfg graph: 1/0

# core name of double operation
coreList = ['DAddSub_nodsp', 'DAddSub_fulldsp', 'DMul_nodsp', 'DMul_fulldsp', 'DMul_maxdsp', 'DDiv', 'DCompare']
opList = ['dadd', 'dsub', 'dmul', 'ddiv', 'dcmp']

# bypass opcode
bypassList = ['br', 'ret', 'phi', 'dacc', 'extractvalue', 'insertvalue',
              'bitconcatenate', 'bitcast', 'trunc', 'sext', 'zext', 'uitofp', 'sitofp', 'uitodp', 'sitodp',
              'alloca', 'read', 'write', 'getelementptr', 'GlobalMem',
              'not_exist']

# focus opcode
focusList = ['add', 'sub', 'mul', 'div', 'dadd', 'dsub', 'dmul', 'ddiv', 'icmp', 'dcmp', 'urem',
             'and', 'or', 'xor', 'lshr', 'shl', 'ashr',
             'select', 'bitselect', 'partselect', 'partset', 'mux', 'switch',
             'load', 'store', 'call']

onehotFlag = 1
n_categ_items = ['op_type', 'node_type']
opcode_categ = ['dadd', 'dsub', 'dmul', 'ddiv', 'call',
                'add', 'sub', 'mul', 'div', 'icmp', 'dcmp', 'urem',
                'and', 'or', 'xor', 'lshr', 'shl', 'ashr',
                'select', 'bitselect', 'partselect', 'partset', 'mux', 'switch',
                'load', 'store']

op_type_categ = [['db_op'], ['sp_op'], ['bit_op'], ['ctr_op'], ['mem_op'], ['none']]
node_type_categ = [['0'], ['1']]

# General edge features
e_num_items = ['edge_type', 'is_back']


def onehot_enc_gen():
    optype_enc = OneHotEncoder(handle_unknown='ignore')
    optype_enc.fit(op_type_categ)  # 6 bits
    node_type_enc = OneHotEncoder(handle_unknown='ignore')
    node_type_enc.fit(node_type_categ)  # 2 bits
    return optype_enc, node_type_enc


def opcode_type(opcode):
    if opcode in {'dadd', 'dsub', 'dmul', 'ddiv', 'call'}:
        t = 'db_op'
    elif opcode in {'add', 'sub', 'mul', 'div', 'icmp', 'dcmp', 'urem'}:
        t = 'sp_op'
    elif opcode in {'and', 'or', 'xor', 'lshr', 'shl', 'ashr'}:
        t = 'bit_op'
    elif opcode in {'select', 'bitselect', 'partselect', 'partset', 'mux', 'switch'}:
        t = 'ctr_op'
    elif opcode in {'load', 'store'}:
        t = 'mem_op'
    else:
        t = 'none'
    return t


def opcode_type_numerical(opcode):
    if opcode in {'dadd', 'dsub', 'dmul', 'ddiv', 'call'}:
        t = 5.0
    elif opcode in {'add', 'sub', 'mul', 'div', 'icmp', 'dcmp', 'urem'}:
        t = 4.0
    elif opcode in {'and', 'or', 'xor', 'lshr', 'shl', 'ashr'}:
        t = 3.0
    elif opcode in {'select', 'bitselect', 'partselect', 'partset', 'mux', 'switch'}:
        t = 2.0
    elif opcode in {'load', 'store'}:
        t = 1.0
    else:
        t = 0.0
    return t


def generate_pyg_dot(DG, dot_store_path, n_num_items):
    pyg_DG = DG.__class__()
    pyg_DG.add_nodes_from(DG)
    pyg_DG.add_edges_from(DG.edges)

    optype_enc, node_type_enc = onehot_enc_gen()

    for node_id in DG.nodes():
        node = DG.nodes[node_id]
        node_feat = list()
        for feat_item in n_num_items:
            if feat_item not in node:
                if feat_item == 'latency':
                    node_feat.extend([0.0, 0.0])
                else:
                    node_feat.append(0.0)
            else:
                if feat_item == 'latency':
                    node_feat.extend([float(node[feat_item][0]), float(node[feat_item][1])])  # 2 latency values
                elif type(node[feat_item]) == int or type(node[feat_item]) == str:
                    node_feat.append(float(node[feat_item]))
                else:
                    print("ERROR: feat_item = {}, not with type str, int or list in node, but with type {}".format
                          (feat_item, type(node[feat_item])))
                    raise AssertionError()

        node_type = node['node_type']
        n_opcode = node['opcode'] if 'opcode' in node else 'none'

        if onehotFlag:
            n_optype = opcode_type(n_opcode)
            onehot_optype = optype_enc.transform([[n_optype]]).toarray()
            onehot_node_type = node_type_enc.transform([[node_type]]).toarray()
            onehot_optype = onehot_optype.reshape(np.shape(onehot_optype)[1])
            onehot_node_type = onehot_node_type.reshape(np.shape(onehot_node_type)[1])

            node_feat = np.concatenate((node_feat, onehot_optype), axis=0)
            node_feat = np.concatenate((node_feat, onehot_node_type), axis=0)  # 14 bits totally
            pyg_DG.nodes[node_id]['x'] = list(node_feat)
        else:
            n_optype = opcode_type_numerical(n_opcode)
            node_type = float(node_type)
            node_feat.extend([n_optype, node_type])  # 8 bits totally
            pyg_DG.nodes[node_id]['x'] = node_feat

    for edge_id in DG.edges():
        edge = DG.edges[edge_id]
        pyg_DG.edges[edge_id]['edge_attr'] = [float(edge['edge_type']), float(edge['is_back_edge'])]

    nx.nx_pydot.write_dot(pyg_DG, dot_store_path)
    return pyg_DG


def set_graph_node_info(DG, node_id, **kwargs):
    graph_node = DG.nodes[node_id]
    for attr_name in kwargs:
        graph_node[attr_name] = kwargs[attr_name]


class CDFG:
    def __init__(self, adb_folder, save_path, bench):
        self.adb_folder = adb_folder
        self.bench = bench
        self.listIRinfo = None
        self.listIRname = None  # IR file name
        # self.list_ret = None  # node_id of ret
        self.call_dict = None  # call node record
        self.submodule_dict = None  # call for submodule
        self.port_to_const_dict = None
        self.op_set = None
        self.cdfg_node_dict = None
        self.cdfg_port_dict = None
        self.cdfg_const_dict = None
        self.cdfg_block_dict = None
        self.cdfg_edge_dict = None
        self.rtl_dict = None
        self.G = None

        self.parse_adb()
        self.cdfg_node_explore(save_path)
        self.cdfg_const_explore(save_path)
        self.cdfg_port_explore(save_path)
        self.cdfg_block_explore(save_path)
        self.cdfg_edge_explore(save_path)
        self.get_rtl_dict(save_path)
        self.fix_resource()
        self.fix_func_call()
        self.get_node_latency()
        self.get_node_resource(save_path)
        self.construct_graph(save_path)
        self.visualize_graph(save_path)

    def parse_adb(self):
        listIRinfo = []
        listIRname = []
        for IRfile in glob.glob(self.adb_folder + '/*.adb'):
            IRname = (IRfile.split('/')[-1]).split('.')[0]
            IRinfo = cET.parse(IRfile).getroot()
            listIRname.append(IRname)
            listIRinfo.append(IRinfo)
        self.listIRinfo = listIRinfo
        self.listIRname = listIRname
        return self.listIRinfo, self.listIRname

    def get_cdfg_node(self):
        cdfg_node_dict = dict()
        op_set = set()
        # list_ret = []
        call_dict = dict()
        prefix = 0  # indicate the identity of adb file
        for IRinfo in self.listIRinfo:
            nodes = IRinfo.find('*/cdfg/nodes')
            for item in nodes.findall('item'):
                node_obj = item.find('Value').find('Obj')
                node_id = str(prefix) + '_' + node_obj.find('id').text
                node_name = node_obj.find('name').text
                node_type = node_obj.find('type').text
                line_num = node_obj.find('lineNumber').text
                rtl_name = node_obj.find('rtlName').text
                op_type = node_obj.find('opType').text
                core_name = node_obj.find('coreName').text

                bitwidth = item.find('Value').find('bitwidth').text
                opcode = item.find('opcode').text
                m_delay = item.find('m_delay').text
                topo_index = item.find('m_topoIndex').text

                oprand_edges = []
                edges = item.find('oprand_edges')
                for edge in edges.findall('item'):
                    oprand_edges.append(edge.text)

                cdfg_node_dict[node_id] = CDFGNode(node_id, node_name, node_type, line_num, rtl_name, op_type,
                                                   core_name, bitwidth, opcode, m_delay, topo_index, oprand_edges)
                if opcode == 'call':
                    if rtl_name is None:
                        rtl_name = 'not_exist'
                    call_node = {node_id: {'prefix': prefix, 'node_name': node_name,
                                           'rtl_name': rtl_name, 'bitwidth': bitwidth}}
                    call_dict.update(call_node)
                op_set.add(opcode)
            prefix += 1
        self.cdfg_node_dict = cdfg_node_dict
        self.op_set = sorted(list(op_set))
        self.call_dict = call_dict
        # self.list_ret = list_ret
        return self.cdfg_node_dict, self.op_set

    def get_cdfg_const(self):
        cdfg_const_dict = dict()
        submodule_dict = dict()
        prefix = 0
        for IRinfo in self.listIRinfo:
            consts = IRinfo.find('*/cdfg/consts')
            for item in consts.findall('item'):
                node_obj = item.find('Value').find('Obj')
                node_id = str(prefix) + '_' + node_obj.find('id').text
                node_name = node_obj.find('name').text
                node_type = node_obj.find('type').text
                line_num = node_obj.find('lineNumber').text
                rtl_name = node_obj.find('rtlName').text
                op_type = node_obj.find('opType').text

                bitwidth = item.find('Value').find('bitwidth').text
                const_type = item.find('const_type').text
                content = item.find('content').text
                if ':' in content:
                    # print(content)
                    content = content.replace(':', ' ')
                    submodule = node_name
                    # submodule_dict.update({submodule: node_id})
                    if prefix not in submodule_dict:
                        submodule_dict[prefix] = {submodule: {'node_id': node_id, 'bitwidth': bitwidth}}
                        # save submodules of the top design
                    else:
                        submodule_dict[prefix].update({submodule: {'node_id': node_id, 'bitwidth': bitwidth}})
                    # print(content)

                cdfg_const_dict[node_id] = CDFGConst(node_id, node_name, node_type, line_num, rtl_name, op_type,
                                                     bitwidth, const_type, content)
            prefix += 1
        self.cdfg_const_dict = cdfg_const_dict
        self.submodule_dict = submodule_dict
        return self.cdfg_const_dict

    def get_cdfg_port(self):
        cdfg_port_dict = dict()
        port_to_const_dict = dict()
        prefix = 0
        for IRinfo in self.listIRinfo:
            ports = IRinfo.find('*/cdfg/ports')
            module = IRinfo.find('*/cdfg/name').text
            for item in ports.findall('item'):
                node_obj = item.find('Value').find('Obj')
                node_id = str(prefix) + '_' + node_obj.find('id').text
                node_name = node_obj.find('name').text
                node_type = node_obj.find('type').text
                line_num = node_obj.find('lineNumber').text
                rtl_name = node_obj.find('rtlName').text
                op_type = node_obj.find('opType').text

                bitwidth = item.find('Value').find('bitwidth').text
                direction = item.find('direction').text
                if_type = item.find('if_type').text
                array_size = item.find('array_size').text

                cdfg_port_dict[node_id] = CDFGPort(node_id, node_name, node_type, line_num, rtl_name, op_type, bitwidth,
                                                   direction, if_type, array_size)
                for prf in self.submodule_dict:
                    if module in self.submodule_dict[prf]:
                        dst_const = self.submodule_dict[prf][module]['node_id']
                        if prf not in port_to_const_dict:
                            port_to_const_dict[prf] = {node_id: {'dst_const': dst_const,
                                                                 'node_name': node_name,
                                                                 'direction': direction,
                                                                 'if_type': if_type}}
                        else:
                            port_to_const_dict[prf].update({node_id: {'dst_const': dst_const,
                                                                      'node_name': node_name,
                                                                      'direction': direction,
                                                                      'if_type': if_type}})
            prefix += 1
        self.cdfg_port_dict = cdfg_port_dict
        self.port_to_const_dict = port_to_const_dict
        return self.cdfg_port_dict

    def get_cdfg_block(self):
        cdfg_block_dict = dict()
        prefix = 0
        for IRinfo in self.listIRinfo:
            blocks = IRinfo.find('*/cdfg/blocks')
            for item in blocks.findall('item'):
                node_obj = item.find('Obj')
                node_id = str(prefix) + '_' + node_obj.find('id').text
                node_name = node_obj.find('name').text
                node_type = node_obj.find('type').text
                line_num = node_obj.find('lineNumber').text
                rtl_name = node_obj.find('rtlName').text
                op_type = node_obj.find('opType').text
                nodes = item.find('node_objs')

                node_objs = []
                for node in nodes.findall('item'):
                    node_objs.append(node.text)

                cdfg_block_dict[node_id] = CDFGBlock(node_id, node_name, node_type, line_num, rtl_name,
                                                     op_type, node_objs)
            prefix += 1
        self.cdfg_block_dict = cdfg_block_dict
        return self.cdfg_block_dict

    def get_cdfg_edge(self):
        cdfg_edge_dict = dict()
        prefix = 0
        for IRinfo in self.listIRinfo:
            edges = IRinfo.find('*/cdfg/edges')
            for edge in edges.findall('item'):
                edge_id = str(prefix) + '_' + edge.find('id').text
                edge_type = edge.find('edge_type').text
                source = str(prefix) + '_' + edge.find('source_obj').text
                sink = str(prefix) + '_' + edge.find('sink_obj').text
                is_back = edge.find('is_back_edge').text

                cdfg_edge_dict[edge_id] = CDFGEdge(edge_id, edge_type, source, sink, is_back)
            prefix += 1
        self.cdfg_edge_dict = cdfg_edge_dict
        return self.cdfg_edge_dict

    def cdfg_node_explore(self, save_path):
        cdfg_node_dict, op_set = self.get_cdfg_node()

        with open('{}/cdfg_node_dict.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            title = ['node_id', 'node_name', 'node_type', 'line_num', 'rtl_name', 'op_type', 'core_name', 'bitwidth',
                     'opcode', 'm_delay', 'topo_index', 'oprand_edges']
            writer.writerow(title)
            for node_id in cdfg_node_dict:
                node = cdfg_node_dict[node_id]
                wr_line = [node.node_id, node.node_name, node.node_type, node.line_num, node.rtl_name, node.op_type,
                           node.core_name, node.bitwidth, node.opcode, node.m_delay, node.topo_index, node.oprand_edges]
                writer.writerow(wr_line)

        with open('{}/op_set.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            for opcode in op_set:
                wr_line = [opcode]
                writer.writerow(wr_line)

    def cdfg_const_explore(self, save_path):
        cdfg_const_dict = self.get_cdfg_const()

        with open('{}/cdfg_const_dict.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            title = ['node_id', 'node_name', 'node_type', 'line_num', 'rtl_name', 'op_type', 'bitwidth', 'const_type',
                     'content']
            writer.writerow(title)
            for node_id in cdfg_const_dict:
                node = cdfg_const_dict[node_id]
                wr_line = [node.node_id, node.node_name, node.node_type, node.line_num, node.rtl_name, node.op_type,
                           node.bitwidth, node.const_type, node.content]
                writer.writerow(wr_line)

    def cdfg_port_explore(self, save_path):
        cdfg_port_dict = self.get_cdfg_port()

        with open('{}/cdfg_port_dict.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            title = ['node_id', 'node_name', 'node_type', 'line_num', 'rtl_name', 'op_type', 'bitwidth', 'direction',
                     'if_type', 'array_size']
            writer.writerow(title)
            for node_id in cdfg_port_dict:
                node = cdfg_port_dict[node_id]
                wr_line = [node.node_id, node.node_name, node.node_type, node.line_num, node.rtl_name, node.op_type,
                           node.bitwidth, node.direction, node.if_type, node.array_size]
                writer.writerow(wr_line)

    def cdfg_block_explore(self, save_path):
        cdfg_block_dict = self.get_cdfg_block()

        with open('{}/cdfg_block_dict.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            title = ['node_id', 'node_name', 'node_type', 'line_num', 'rtl_name', 'op_type', 'node_objs']
            writer.writerow(title)
            for node_id in cdfg_block_dict:
                node = cdfg_block_dict[node_id]
                wr_line = [node.node_id, node.node_name, node.node_type, node.line_num, node.rtl_name, node.op_type,
                           node.node_objs]
                writer.writerow(wr_line)

    def cdfg_edge_explore(self, save_path):
        cdfg_edge_dict = self.get_cdfg_edge()

        with open('{}/cdfg_edge_dict.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            title = ['edge_id', 'edge_type', 'source_obj', 'sink_obj', 'is_back_edge']
            writer.writerow(title)
            for edge_id in cdfg_edge_dict:
                edge = cdfg_edge_dict[edge_id]
                wr_line = [edge.edge_id, edge.edge_type, edge.source, edge.sink, edge.is_back]
                writer.writerow(wr_line)

    def get_rtl_dict(self, save_path):
        """
        return:
            rtl_dict: This file returns a hash table of resources and the rtlNames.
        """
        rtl_dict = dict()
        for IRinfo in self.listIRinfo:
            all_rtl = IRinfo.find('*/res')
            component = all_rtl.find('dp_component_resource')
            expression = all_rtl.find('dp_expression_resource')
            fifo = all_rtl.find('dp_fifo_resource')
            memory = all_rtl.find('dp_memory_resource')
            multiplexer = all_rtl.find('dp_multiplexer_resource')
            register = all_rtl.find('dp_register_resource')

            for item in component.findall('item'):
                rtl_name = item.find('first').text
                rtl_name = rtl_name.split(' ')[0]
                rtl_res = item.find('second')
                if rtl_name not in rtl_dict:
                    rtl_dict[rtl_name] = Component(rtl_name, 'component')
                    for res in rtl_res.findall('item'):
                        if res.find('first').text == 'DSP':
                            rtl_dict[rtl_name].dsp = res.find('second').text
                        elif res.find('first').text == 'FF':
                            rtl_dict[rtl_name].ff = res.find('second').text
                        elif res.find('first').text == 'LUT':
                            rtl_dict[rtl_name].lut = res.find('second').text
                        elif res.find('first').text == 'URAM':
                            rtl_dict[rtl_name].uram = res.find('second').text
                        elif res.find('first').text == 'BRAM_18K':
                            rtl_dict[rtl_name].bram = res.find('second').text

            for item in expression.findall('item'):
                rtl_name = item.find('first').text
                operation = rtl_name.split(' ')[2]
                rtl_name = rtl_name.split(' ')[0]
                rtl_res = item.find('second')
                if rtl_name not in rtl_dict:
                    rtl_dict[rtl_name] = Component(rtl_name, 'expression')
                    rtl_dict[rtl_name].operation = operation
                    for res in rtl_res.findall('item'):
                        if res.find('first').text == 'DSP':
                            rtl_dict[rtl_name].dsp = res.find('second').text
                        elif res.find('first').text == 'FF':
                            rtl_dict[rtl_name].ff = res.find('second').text
                        elif res.find('first').text == 'LUT':
                            rtl_dict[rtl_name].lut = res.find('second').text
                        elif res.find('first').text == '(0P0)':
                            rtl_dict[rtl_name].bitwidth_p0 = res.find('second').text
                        elif res.find('first').text == '(1P1)':
                            rtl_dict[rtl_name].bitwidth_p1 = res.find('second').text

            for item in fifo.findall('item'):
                rtl_name = item.find('first').text
                rtl_res = item.find('second')
                if rtl_name not in rtl_dict:
                    rtl_dict[rtl_name] = Component(rtl_name, 'fifo')
                    for res in rtl_res.findall('item'):
                        if res.find('first').text == 'FF':
                            rtl_dict[rtl_name].ff = res.find('second').text
                        elif res.find('first').text == 'LUT':
                            rtl_dict[rtl_name].lut = res.find('second').text
                        elif res.find('first').text == 'URAM':
                            rtl_dict[rtl_name].uram = res.find('second').text
                        elif res.find('first').text == 'BRAM_18K':
                            rtl_dict[rtl_name].bram = res.find('second').text
                        elif res.find('first').text == 'Depth':
                            rtl_dict[rtl_name].ff_depth = res.find('second').text
                        elif res.find('first').text == 'Bits':
                            rtl_dict[rtl_name].ff_bits = res.find('second').text
                        elif res.find('first').text == 'Size':
                            rtl_dict[rtl_name].ff_size = res.find('second').text

            for item in memory.findall('item'):
                rtl_name = item.find('first').text
                rtl_res = item.find('second')
                if rtl_name not in rtl_dict:
                    rtl_dict[rtl_name] = Component(rtl_name, 'memory')
                    for res in rtl_res.findall('item'):
                        if res.find('first').text == 'FF':
                            rtl_dict[rtl_name].ff = res.find('second').text
                        elif res.find('first').text == 'LUT':
                            rtl_dict[rtl_name].lut = res.find('second').text
                        elif res.find('first').text == 'URAM':
                            rtl_dict[rtl_name].uram = res.find('second').text
                        elif res.find('first').text == 'BRAM_18K':
                            rtl_dict[rtl_name].bram = res.find('second').text
                        elif res.find('first').text == '(0Words)':
                            rtl_dict[rtl_name].mem_words = res.find('second').text
                        elif res.find('first').text == '(1Bits)':
                            rtl_dict[rtl_name].mem_bits = res.find('second').text
                        elif res.find('first').text == '(2Banks)':
                            rtl_dict[rtl_name].mem_banks = res.find('second').text
                        elif res.find('first').text == '(3W*Bits*Banks)':
                            rtl_dict[rtl_name].mem_wxbitsxbanks = res.find('second').text

            for item in multiplexer.findall('item'):
                # TODO: rename rtl_name
                rtl_name = item.find('first').text + '_mux'
                rtl_res = item.find('second')
                if rtl_name not in rtl_dict:
                    rtl_dict[rtl_name] = Component(rtl_name, 'multiplexer')
                    for res in rtl_res.findall('item'):
                        if res.find('first').text == 'LUT':
                            rtl_dict[rtl_name].lut = res.find('second').text
                        elif res.find('first').text == '(0Size)':
                            rtl_dict[rtl_name].mux_inputsize = res.find('second').text
                        elif res.find('first').text == '(1Bits)':
                            rtl_dict[rtl_name].mux_bits = res.find('second').text
                        elif res.find('first').text == '(2Count)':
                            rtl_dict[rtl_name].mux_totalbits = res.find('second').text

            for item in register.findall('item'):
                # TODO: rename rtl_name
                rtl_name = item.find('first').text
                rtl_res = item.find('second')
                if rtl_name not in rtl_dict:
                    rtl_dict[rtl_name] = Component(rtl_name, 'register')
                    for res in rtl_res.findall('item'):
                        if res.find('first').text == 'FF':
                            rtl_dict[rtl_name].ff = res.find('second').text
                        elif res.find('first').text == 'LUT':
                            rtl_dict[rtl_name].lut = res.find('second').text
                        elif res.find('first').text == '(Bits)':
                            rtl_dict[rtl_name].reg_bits = res.find('second').text
                        elif res.find('first').text == '(Consts)':
                            rtl_dict[rtl_name].reg_const_bits = res.find('second').text
        self.rtl_dict = rtl_dict

        # output rtl resource
        with open('{}/resource_dict.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            title = ['rtl_name', 'lut', 'ff', 'dsp', 'bram', 'uram']
            writer.writerow(title)
            for rtl_name in self.rtl_dict:
                rtl = self.rtl_dict[rtl_name]
                wr_line = [rtl_name, rtl.lut, rtl.ff, rtl.dsp, rtl.bram, rtl.uram]
                writer.writerow(wr_line)

        return self.rtl_dict

    def fix_resource(self):
        for node_id in self.cdfg_node_dict:
            node = self.cdfg_node_dict[node_id]
            opcode = node.opcode
            rtl_name = node.rtl_name
            if (opcode in opList) and (rtl_name == 'not_exist'):
                core_name = node.core_name
                if core_name in coreList:
                    if core_name == 'DAddSub_nodsp':
                        key1 = 'dadddsub'
                        key2 = 'no'
                        key3 = 'dsp'
                        for rtl_name_real in self.rtl_dict:
                            if (key1 in rtl_name_real) and (key2 in rtl_name_real) and (key3 in rtl_name_real):
                                node.rtl_name = rtl_name_real
                                break
                            elif ('dadd' in rtl_name_real) and (key2 in rtl_name_real) and (key3 in rtl_name_real):
                                node.rtl_name = rtl_name_real
                                break
                            elif ('dsub' in rtl_name_real) and (key2 in rtl_name_real) and (key3 in rtl_name_real):
                                node.rtl_name = rtl_name_real
                                break
                    elif core_name == 'DAddSub_fulldsp':
                        key1 = 'dadddsub'
                        key2 = 'full'
                        key3 = 'dsp'
                        for rtl_name_real in self.rtl_dict:
                            if (key1 in rtl_name_real) and (key2 in rtl_name_real) and (key3 in rtl_name_real):
                                node.rtl_name = rtl_name_real
                                break
                            elif ('dadd' in rtl_name_real) and (key2 in rtl_name_real) and (key3 in rtl_name_real):
                                node.rtl_name = rtl_name_real
                                break
                    elif core_name == 'DMul_nodsp':
                        key1 = 'dmul'
                        key2 = 'no'
                        key3 = 'dsp'
                        for rtl_name_real in self.rtl_dict:
                            if (key1 in rtl_name_real) and (key2 in rtl_name_real) and (key3 in rtl_name_real):
                                node.rtl_name = rtl_name_real
                                break
                    elif core_name == 'DMul_fulldsp':
                        key1 = 'dmul'
                        key2 = 'full'
                        key3 = 'dsp'
                        for rtl_name_real in self.rtl_dict:
                            if (key1 in rtl_name_real) and (key2 in rtl_name_real) and (key3 in rtl_name_real):
                                node.rtl_name = rtl_name_real
                                break
                    elif core_name == 'DMul_maxdsp':
                        key1 = 'dmul'
                        key2 = 'max'
                        key3 = 'dsp'
                        for rtl_name_real in self.rtl_dict:
                            if (key1 in rtl_name_real) and (key2 in rtl_name_real) and (key3 in rtl_name_real):
                                node.rtl_name = rtl_name_real
                                break
                    elif core_name == 'DDiv':
                        key1 = 'ddiv'
                        for rtl_name_real in self.rtl_dict:
                            if key1 in rtl_name_real:
                                node.rtl_name = rtl_name_real
                                break
                    elif core_name == 'DCompare':
                        key1 = 'dcmp'
                        for rtl_name_real in self.rtl_dict:
                            if key1 in rtl_name_real:
                                node.rtl_name = rtl_name_real
                                break
                    if node.rtl_name == 'not_exist':
                        print('Core exists but no rtl module! --> ' + node_id)
                else:
                    print('Check if the core name is ignored! --> ' + core_name)

    def fix_func_call(self):
        for node_id in self.call_dict:
            call_node = self.call_dict[node_id]
            rtl_name = call_node['rtl_name']
            # tag = rtl_name.split('_')[0]
            if rtl_name == 'not_exist':
                # print('Invalid rtl_name: not_exist')
                prefix = call_node['prefix']
                bitwidth = call_node['bitwidth']
                prf_group = self.submodule_dict[prefix]
                for rtl in prf_group:
                    if prf_group[rtl]['bitwidth'] == bitwidth:
                        rtl_type = 'grp_' + rtl
                        for key in self.rtl_dict:
                            if rtl_type in key:
                                rtl_name = key
                                self.cdfg_node_dict[node_id].rtl_name = rtl_name
                                break
                if rtl_name == 'not_exist':
                    print('Failed to match rtl_name!')
            # elif tag != 'grp':
            #     print('Mistake in rtl_name: not_grp but ' + rtl_name)

    def get_node_latency(self):
        prefix = 0
        for IRinfo in self.listIRinfo:
            node_latency = IRinfo.find('*/node_label_latency')
            for item in node_latency.findall('item'):
                node_id = str(prefix) + '_' + item.find('first').text
                if node_id in self.cdfg_node_dict:
                    second = item.find('second')
                    l1 = second.find('first').text
                    l2 = second.find('second').text
                    latency = [l1, l2]
                    self.cdfg_node_dict[node_id].latency = latency
            prefix += 1
        return self.cdfg_node_dict

    def get_node_resource(self, save_path):
        for node_id in self.cdfg_node_dict:
            rtl_name = self.cdfg_node_dict[node_id].rtl_name
            if rtl_name in self.rtl_dict:
                self.cdfg_node_dict[node_id].lut = self.rtl_dict[rtl_name].lut
                self.cdfg_node_dict[node_id].ff = self.rtl_dict[rtl_name].ff
                self.cdfg_node_dict[node_id].dsp = self.rtl_dict[rtl_name].dsp
                self.cdfg_node_dict[node_id].bram = self.rtl_dict[rtl_name].bram
                self.cdfg_node_dict[node_id].uram = self.rtl_dict[rtl_name].uram

        # add resource information
        with open('{}/cdfg_node_resource_dict.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            title = ['node_id', 'node_name', 'node_type', 'line_num', 'rtl_name', 'op_type', 'core_name', 'bitwidth',
                     'opcode', 'm_delay', 'topo_index', 'oprand_edges', 'latency', 'lut', 'ff', 'dsp', 'bram', 'uram']
            writer.writerow(title)
            for node_id in self.cdfg_node_dict:
                node = self.cdfg_node_dict[node_id]
                wr_line = [node.node_id, node.node_name, node.node_type, node.line_num, node.rtl_name, node.op_type,
                           node.core_name, node.bitwidth, node.opcode, node.m_delay, node.topo_index, node.oprand_edges,
                           node.latency, node.lut, node.ff, node.dsp, node.bram, node.uram]
                writer.writerow(wr_line)

        return self.cdfg_node_dict

    def connect_submodule(self):
        # run llvm-dis to get ll file
        # llvm-dis a.o.3.bc -o a.o.3.ll
        # bc_path = os.path.join(self.adb_folder, 'a.o.3.bc')
        # ll_path = os.path.join(self.adb_folder, 'a.o.3.ll')
        # if os.path.exists(ll_path):
        #     pass
        # else:
        #     pass
        # f_ll = open(ll_path, 'r')
        # for line in f_ll.readlines():
        for prf in self.port_to_const_dict:
            cur_dict = self.port_to_const_dict[prf]
            for node_id in cur_dict:
                port = cur_dict[node_id]
                dst_const = port['dst_const']
                # direction = port['direction']
                self.G.add_edge(node_id, dst_const, edge_id='0', edge_type='0', is_back_edge='0')

    def bypass_op(self):
        rm_node_list = list()

        for node_id in self.G.nodes:
            node_type = self.G.nodes[node_id]['node_type']
            if int(node_type) == 0:  # node
                opcode = self.G.nodes[node_id]['opcode']
                if opcode in bypassList:
                    for pre_id in list(self.G.predecessors(node_id)):
                        for suc_id in list(self.G.successors(node_id)):
                            if self.G.has_edge(pre_id, suc_id):
                                pass
                            else:
                                edge = self.G[pre_id][node_id]
                                edge_id = edge['edge_id']
                                edge_type = edge['edge_type']
                                is_back_edge = edge['is_back_edge']
                                self.G.add_edge(pre_id, suc_id, edge_id=edge_id, edge_type=edge_type,
                                                is_back_edge=is_back_edge)
                    rm_node_list.append(node_id)
                elif opcode == 'bitselect' or opcode == 'partselect':
                    rtl_name = self.G.nodes[node_id]['rtl_name']
                    if 'reg' not in rtl_name:
                        for pre_id in list(self.G.predecessors(node_id)):
                            for suc_id in list(self.G.successors(node_id)):
                                if self.G.has_edge(pre_id, suc_id):
                                    pass
                                else:
                                    edge = self.G[pre_id][node_id]
                                    edge_id = edge['edge_id']
                                    edge_type = edge['edge_type']
                                    is_back_edge = edge['is_back_edge']
                                    self.G.add_edge(pre_id, suc_id, edge_id=edge_id, edge_type=edge_type,
                                                    is_back_edge=is_back_edge)
                        rm_node_list.append(node_id)
                # elif opcode == 'load' or opcode == 'store' or opcode == 'shl':
                elif opcode == 'shl':
                    core_name = self.G.nodes[node_id]['core_name']
                    if core_name == 'not_exist':
                        for pre_id in list(self.G.predecessors(node_id)):
                            for suc_id in list(self.G.successors(node_id)):
                                if self.G.has_edge(pre_id, suc_id):
                                    pass
                                else:
                                    edge = self.G[pre_id][node_id]
                                    edge_id = edge['edge_id']
                                    edge_type = edge['edge_type']
                                    is_back_edge = edge['is_back_edge']
                                    self.G.add_edge(pre_id, suc_id, edge_id=edge_id, edge_type=edge_type,
                                                    is_back_edge=is_back_edge)
                        rm_node_list.append(node_id)
            elif int(node_type) == 2 or int(node_type) == 3:  # const or block
                for pre_id in list(self.G.predecessors(node_id)):
                    for suc_id in list(self.G.successors(node_id)):
                        if self.G.has_edge(pre_id, suc_id):
                            pass
                        else:
                            edge = self.G[pre_id][node_id]
                            edge_id = edge['edge_id']
                            edge_type = edge['edge_type']
                            is_back_edge = edge['is_back_edge']
                            self.G.add_edge(pre_id, suc_id, edge_id=edge_id, edge_type=edge_type,
                                            is_back_edge=is_back_edge)
                rm_node_list.append(node_id)

        self.G.remove_nodes_from(rm_node_list)

    def construct_graph(self, save_path):
        G = nx.DiGraph()
        # find edges and build the graph
        # print("Adding Edges")
        for edge_id in self.cdfg_edge_dict:
            edge = self.cdfg_edge_dict[edge_id]
            G.add_edge(edge.source, edge.sink, edge_id=edge.edge_id, edge_type=edge.edge_type,
                       is_back_edge=edge.is_back)

        # add node attributes
        # print("Adding Nodes")
        for node_id in self.cdfg_node_dict:
            if node_id in G.nodes():
                node = self.cdfg_node_dict[node_id]
                G.add_node(node_id)
                set_graph_node_info(G, node_id, node_name=node.node_name, node_type=node.node_type,
                                    line_num=node.line_num, rtl_name=node.rtl_name, op_type=node.op_type,
                                    core_name=node.core_name, bitwidth=node.bitwidth, opcode=node.opcode,
                                    m_delay=node.m_delay, topo_index=node.topo_index, oprand_edges=node.oprand_edges,
                                    latency=node.latency, lut=node.lut, ff=node.ff,
                                    dsp=node.dsp, bram=node.bram, uram=node.uram)

        # add ports for function arguments
        # print("Adding Ports")
        for node_id in self.cdfg_port_dict:
            if node_id in G.nodes():
                port = self.cdfg_port_dict[node_id]
                G.add_node(node_id)
                set_graph_node_info(G, node_id, node_name=port.node_name, node_type=port.node_type,
                                    line_num=port.line_num, rtl_name=port.rtl_name, op_type=port.op_type,
                                    bitwidth=port.bitwidth, direction=port.direction, if_type=port.if_type,
                                    array_size=port.array_size)

        # blocks for control signals
        if blockFlag:
            # print("Adding Basic Blocks")
            for node_id in self.cdfg_block_dict:
                if node_id in G.nodes():
                    block = self.cdfg_block_dict[node_id]
                    G.add_node(node_id)
                    set_graph_node_info(G, node_id, node_name=block.node_name, node_type=block.node_type,
                                        line_num=block.line_num, rtl_name=block.rtl_name, op_type=block.op_type,
                                        node_objs=block.node_objs)
        else:
            print('Basic Blocks Are Ignored!')

        # consts are necessary
        if constFlag:
            # print("Adding Consts")
            for node_id in self.cdfg_const_dict:
                if node_id in G.nodes():
                    const = self.cdfg_const_dict[node_id]
                    G.add_node(node_id)
                    set_graph_node_info(G, node_id, node_name=const.node_name, node_type=const.node_type,
                                        line_num=const.line_num, rtl_name=const.rtl_name, op_type=const.op_type,
                                        bitwidth=const.bitwidth, const_type=const.const_type, content=const.content)
        else:
            print("Merge Consts to Other Nodes")
            for node_id in self.cdfg_const_dict:
                if node_id in G.nodes():
                    for v in G.neighbors(node_id):
                        G.nodes[v]['const'] = node_id
                    G.remove_node(node_id)

        G.remove_nodes_from(list(nx.isolates(G)))
        empty_node = []  # record empty nodes then remove them
        for node_id in G.nodes():
            if not G.nodes[node_id]:
                # print(node_id)
                empty_node.append(node_id)
        G.remove_nodes_from(empty_node)

        self.G = G
        self.connect_submodule()
        self.bypass_op()

        self.G.remove_nodes_from(list(nx.isolates(self.G)))

        # output the reduced node dict
        with open('{}/cdfg_node_reduced_dict.csv'.format(save_path), 'w+', newline='') as wfile:
            writer = csv.writer(wfile)
            title = ['node_id', 'node_name', 'node_type', 'line_num', 'rtl_name', 'op_type', 'core_name', 'bitwidth',
                     'opcode', 'm_delay', 'topo_index', 'oprand_edges', 'latency', 'lut', 'ff', 'dsp', 'bram', 'uram']
            writer.writerow(title)
            for node_id in self.G.nodes():
                node = self.G.nodes[node_id]
                if int(node['node_type']) == 0:
                    wr_line = [node_id, node['node_name'], node['node_type'], node['line_num'], node['rtl_name'],
                               node['op_type'], node['core_name'], node['bitwidth'], node['opcode'], node['m_delay'],
                               node['topo_index'], node['oprand_edges'], node['latency'], node['lut'], node['ff'],
                               node['dsp'], node['bram'], node['uram']]
                    writer.writerow(wr_line)

        return self.G

    def visualize_graph(self, save_path):
        nx.nx_pydot.write_dot(self.G, '{}/G.dot'.format(save_path))
        if plotFlag:
            gvz_graph = gvz.Digraph(format='png', filename='{}/test_G'.format(save_path))
            gvz_graph.attr('node', fontsize='20')
            gvz_graph.attr('edge', arrowsize='1', fontsize='20')
            G = self.G
            N = G.nodes()
            E = G.edges()
            for node_id in N:
                node = G.nodes[node_id]
                if node == dict():
                    continue
                elif int(node['node_type']) == 0:  # node
                    if node['opcode'] == 'ret':
                        # print(node_id + ' has ret opcode')
                        gvz_graph.attr('node', style='filled', colorscheme='set28', color='5')
                    else:
                        gvz_graph.attr('node', style='filled', colorscheme='set28', color='1')
                    gvz_graph.node(node_id, label=node['opcode'])
                elif int(node['node_type']) == 1:  # port
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='2')
                    gvz_graph.node(node_id, label=node['node_name'])
                elif int(node['node_type']) == 2:  # const
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='3')
                    gvz_graph.node(node_id, label=node['node_name'])
                elif int(node['node_type']) == 3:  # block
                    gvz_graph.attr('node', style='filled', colorscheme='set28', color='4')
                    gvz_graph.node(node_id, label=node['node_name'])
            for edge_id in E:
                gvz_graph.edge(edge_id[0], edge_id[1])

            gvz_graph.render(view=False)


class CDFGNode:
    def __init__(self, node_id, node_name, node_type, line_num, rtl_name, op_type, core_name, bitwidth, opcode, m_delay,
                 topo_index, oprand_edges, latency=None, lut=0, ff=0, dsp=0, bram=0, uram=0):
        self.node_id = node_id  # node id
        self.node_name = node_name  # node name
        self.node_type = node_type  # node type
        self.line_num = line_num  # node line number in C code
        if rtl_name is None:  # node impl rtl
            self.rtl_name = 'not_exist'
        else:
            self.rtl_name = rtl_name
        if op_type is None:  # node op type in rtl
            self.op_type = 'not_exist'
        else:
            self.op_type = op_type
        if core_name is None:
            self.core_name = 'not_exist'
        else:
            self.core_name = core_name
        self.bitwidth = bitwidth  # node bitwidth
        self.opcode = opcode  # node opcode
        self.m_delay = m_delay  # delay in this node
        self.topo_index = topo_index  # topology index of the node
        self.oprand_edges = oprand_edges  # oprands in this node (number is used)

        if latency is None:
            self.latency = []
        else:
            self.latency = latency  # average of latency is used
        self.lut = lut
        self.ff = ff
        self.dsp = dsp
        self.bram = bram
        self.uram = uram


class CDFGPort:
    def __init__(self, node_id, node_name, node_type, line_num, rtl_name, op_type, bitwidth, direction, if_type,
                 array_size):
        self.node_id = node_id
        self.node_name = node_name
        self.node_type = node_type
        self.line_num = line_num
        if rtl_name is None:
            self.rtl_name = 'not_exist'
        else:
            self.rtl_name = rtl_name
        if op_type is None:
            self.op_type = 'not_exist'
        else:
            self.op_type = op_type
        self.bitwidth = bitwidth
        self.direction = direction  # port direction (in/out, 0/1)
        self.if_type = if_type  # TODO: the meaning
        self.array_size = array_size  # array size of port


class CDFGConst:
    def __init__(self, node_id, node_name, node_type, line_num, rtl_name, op_type, bitwidth, const_type, content):
        self.node_id = node_id
        self.node_name = node_name
        self.node_type = node_type
        self.line_num = line_num
        if rtl_name is None:
            self.rtl_name = 'not_exist'
        else:
            self.rtl_name = rtl_name
        if op_type is None:
            self.op_type = 'not_exist'
        else:
            self.op_type = op_type
        self.bitwidth = bitwidth
        self.const_type = const_type  # type of const
        self.content = content  # const content


class CDFGBlock:
    def __init__(self, node_id, node_name, node_type, line_num, rtl_name, op_type, node_objs):
        self.node_id = node_id
        self.node_name = node_name
        self.node_type = node_type
        self.line_num = line_num
        if rtl_name is None:
            self.rtl_name = 'not_exist'
        else:
            self.rtl_name = rtl_name
        if op_type is None:
            self.op_type = 'not_exist'
        else:
            self.op_type = op_type
        self.node_objs = node_objs  # nodes in the block (number is used)


class CDFGEdge:
    def __init__(self, edge_id, edge_type, source, sink, is_back):
        self.edge_id = edge_id
        self.edge_type = edge_type
        self.source = source
        self.sink = sink
        self.is_back = is_back


class Component:
    def __init__(self, cp_name, cp_type):
        self.cp_name = cp_name
        self.cp_type = cp_type

        self.bram = 0
        self.dsp = 0
        self.ff = 0
        self.lut = 0
        self.uram = 0

        self.mem_words = 0
        self.mem_bits = 0
        self.mem_banks = 0
        self.mem_wxbitsxbanks = 0

        self.ff_depth = 0
        self.ff_bits = 0
        self.ff_size = 0

        self.operation = ''
        self.bitwidth_p0 = 0
        self.bitwidth_p1 = 0

        self.mux_inputsize = 0
        self.mux_bits = 0
        self.mux_totalbits = 0

        self.reg_bits = 0
        self.reg_const_bits = 0


def generate_dataframe(DG, hls_attr, df_store_path):

    data = {'x': {}, 'edge_attr': {}}
    for node_id in DG.nodes():
        node = DG.nodes[node_id]
        data['x'] = data['x'] + [node['x']] if data['x'] else [node['x']]
    for edge_id in DG.edges():
        edge = DG.edges[edge_id]
        data['edge_attr'] = data['edge_attr'] + [edge['edge_attr']] if data['edge_attr'] else [edge['edge_attr']]

    for key, item in data.items():
        try:
            data[key] = torch.tensor(item)
        except ValueError:
            pass

    edge_index = torch.LongTensor(list(DG.edges)).t().contiguous()
    data['edge_index'] = edge_index.view(2, -1)
    data['hls_attr'] = torch.tensor([hls_attr])

    dataframe = Data.from_dict(data)
    torch.save(dataframe, df_store_path)

    return dataframe
