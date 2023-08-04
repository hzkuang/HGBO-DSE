# four types of vertex (node/port/const/block) and one type of edge in original adb files
# post-HLS RTL components utilization


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
