import os
import glob
import shutil
from common import createFolder


def get_adb_rpt_verilog(case, top, alg, ori_prj_path, dataset_path, iterNum, process, mode):
    ir_path = case + '_' + alg + '_prj_p{}/solution/.autopilot/db/'.format(str(process))
    prj_path = os.path.join(dataset_path, 'prj_%d' % iterNum)
    if not os.path.isdir(dataset_path):
        createFolder(dataset_path)
    createFolder(prj_path)
    graph_path = os.path.join(prj_path, 'graph')
    report_path = os.path.join(prj_path, 'report')

    createFolder(graph_path)
    createFolder(report_path)

    for adb_file in glob.glob(os.path.join(ori_prj_path, ir_path) + '*.adb'):
        if 'bind' not in adb_file and 'sched' not in adb_file:
            func_name = (adb_file.split('/')[-1]).split('.')[0]
            adb_path_ori = os.path.join(ori_prj_path, ir_path + func_name + '.adb')
            adb_xml_path_ori = os.path.join(ori_prj_path, ir_path + func_name + '.adb.xml')
            shutil.copy(adb_path_ori, graph_path)
            shutil.copy(adb_xml_path_ori, graph_path)

    # copy ll and bc files
    bc_path = os.path.join(ori_prj_path, ir_path, 'a.o.3.bc')
    ll_path = os.path.join(ori_prj_path, ir_path, 'apatb_' + top + '_ir.ll')
    if os.path.exists(bc_path):
        shutil.copy(bc_path, graph_path)
    if os.path.exists(ll_path):
        shutil.copy(ll_path, graph_path)

    # copy hls reports
    verbose_rpt = os.path.join(ori_prj_path, ir_path, top + '.verbose.rpt')
    verbose_xml = verbose_rpt + '.xml'
    csyn_path = case + '_' + alg + '_prj_p{}/solution/syn/report'.format(str(process))
    hls_rpt = os.path.join(ori_prj_path, csyn_path, top + '_csynth.rpt')
    hls_xml = os.path.join(ori_prj_path, csyn_path, top + '_csynth.xml')
    hls_rpt_full = os.path.join(ori_prj_path, csyn_path, 'csynth.rpt')
    hls_xml_full = os.path.join(ori_prj_path, csyn_path, 'csynth.xml')
    solution_path = case + '_' + alg + '_prj_p{}/solution'.format(str(process))
    directive_record = os.path.join(ori_prj_path, solution_path, 'solution.directive')
    solution_log = os.path.join(ori_prj_path, solution_path, 'solution.log')
    solution_data = os.path.join(ori_prj_path, solution_path, 'solution_data.json')
    hls_rpt_list = [verbose_rpt, verbose_xml, hls_rpt, hls_xml, hls_rpt_full, hls_xml_full, directive_record,
                    solution_log, solution_data]
    for hls_idx in hls_rpt_list:
        if os.path.exists(hls_idx):
            shutil.copy(hls_idx, report_path)

    if mode == 'impl':
        verilog_path = os.path.join(prj_path, 'verilog')
        createFolder(verilog_path)
        # copy Verilog files
        verilog_folder = ''.join([case, '_', alg, '_prj_p{}/solution/syn/verilog'.format(str(process))])
        ori_verilog_path = os.path.join(ori_prj_path, verilog_folder)
        veri_list = os.listdir(ori_verilog_path)
        for veri_idx in veri_list:
            veri_src = os.path.join(ori_verilog_path, veri_idx)
            shutil.copy(veri_src, verilog_path)

        # copy syn/impl reports
        syn_rpt = os.path.join(ori_prj_path, case + '_' + alg +
                               "_prj_p{}/solution/impl/report/verilog/export_syn.rpt".format(str(process)))
        syn_xml = os.path.join(ori_prj_path, case + '_' + alg +
                               "_prj_p{}/solution/impl/report/verilog/export_syn.xml".format(str(process)))
        impl_rpt = os.path.join(ori_prj_path, case + '_' + alg +
                                "_prj_p{}/solution/impl/report/verilog/export_impl.rpt".format(str(process)))
        impl_xml = os.path.join(ori_prj_path, case + '_' + alg +
                                "_prj_p{}/solution/impl/report/verilog/export_impl.xml".format(str(process)))
        simple_impl_rpt = os.path.join(ori_prj_path, case + '_' + alg +
                                       "_prj_p{}/solution/impl/report/verilog/".format(str(process))
                                       + top + "_export.rpt")
        power_rpt = os.path.join(ori_prj_path, case + '_' + alg +
                                 "_prj_p{}/solution/impl/verilog/project.runs/impl_1/bd_0_wrapper_power_routed.rpt".
                                 format(str(process)))
        impl_rpt_list = [syn_rpt, syn_xml, impl_rpt, impl_xml, simple_impl_rpt, power_rpt]
        for impl_idx in impl_rpt_list:
            if os.path.exists(impl_idx):
                shutil.copy(impl_idx, report_path)
        rpt_list = [hls_rpt, hls_xml, syn_rpt, simple_impl_rpt, power_rpt]
    else:
        rpt_list = [hls_rpt, hls_xml]

    return rpt_list, prj_path
