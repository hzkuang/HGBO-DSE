import networkx as nx
import numpy as np
from sklearn.preprocessing import OneHotEncoder

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
