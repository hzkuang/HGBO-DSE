import optuna
import argparse
import subprocess
import pyDOE
from alg.sa_sampler import SimulatedAnnealingSampler
from hls_basic import HLSBasic
from tdm.gen_config import *
from tdm.design_space import *
from hgp_pred import *
from get_ppa import *
from save_report import *
import sys
sys.path.append("./alg")
print(sys.path)


noLatList = ['bfs', 'fft', 'nw', 'stencil']


def objective(trial):
    global basic
    # get the global variables from basic
    dataset_path = basic.dataset_path
    static_config = basic.static_config
    params = basic.params
    ori_prj_path = basic.ori_prj_path
    hls_temp = basic.hls_temp
    hls_script_path = basic.hls_script_path
    case = basic.case
    top = basic.top
    alg = basic.alg
    encode = basic.encode
    process = basic.process
    mode = basic.mode

    tempDir, paraDict = config_tree_space(static_config, encode, trial, params)
    print(paraDict)

    # generate tcl for HLS
    iterNum = trial.number
    dir_json = os.path.join(hls_script_path, "dir_%d.json" % iterNum)
    dir_tcl = os.path.join(hls_script_path, "dir_%d.tcl" % iterNum)
    hls_tcl = os.path.join(hls_script_path, "hls_%d.tcl" % iterNum)
    genDirConfig(encode, params, static_config, paraDict, dir_tcl, tempDir, dir_json)
    f_script = open(hls_temp, "r")
    content = f_script.read()
    f_script.close()
    content = content.replace('dir_test.tcl', 'dir_%d.tcl' % iterNum)
    f_script = open(hls_tcl, "w")
    f_script.write(content)
    f_script.close()
    if mode == 'hgp':
        print("Running Vitis HLS to get adb and adb.xml files...")
        p = subprocess.Popen('vitis_hls -f ' + hls_tcl, shell=True)
        try:
            p.wait(3600)
        except subprocess.TimeoutExpired:
            p.terminate()
            print("[INFO] Subprocess timeout !")
            with open('./runtime.log', 'a') as tlog:
                tlog.write(("Iteration: %d, Timeout !" % iterNum) + '\n')
        print("Using HGP to predict PPA values...")
        rpt_list, prj_path = get_adb_rpt_verilog(case, top, alg, ori_prj_path, dataset_path, iterNum, process, mode)
        dictPPA, fail_flag = getHLS(params, rpt_list)  # get results from HLS
        if fail_flag:
            dictPPA['IMPL'] = {'LUT': 1e8, 'FF': 1e8, 'DSP': 1e8, 'BRAM': 1e8, 'CP': 1e8, 'PWR': 1e8}
        else:
            dict_hls = dictPPA['HLS']
            hls_attr = list(dict_hls.values())
            dictPPA['IMPL'] = getGNNPred(prj_path, hls_attr, case)
    else:
        print("Running Vitis HLS and Vivado to get PPA...")
        p = subprocess.Popen('vitis_hls -f ' + hls_tcl, shell=True)
        try:
            p.wait(3600)
        except subprocess.TimeoutExpired:
            p.terminate()
            print("[INFO] Subprocess timeout !")
            with open('./runtime.log', 'a') as tlog:
                tlog.write(("Iteration: %d, Timeout !" % iterNum) + '\n')
        print("Collecting adb files, hls/syn/impl report and Verilog files...")
        rpt_list, _ = get_adb_rpt_verilog(case, top, alg, ori_prj_path, dataset_path, iterNum, process, mode)
        dictPPA, _ = getPPA(params, rpt_list)

    ppa_rpt = os.path.join(hls_script_path, "ppa_%d.json" % iterNum)
    with open(ppa_rpt, "w") as fout:
        fout.write(json.dumps(dictPPA, indent=4))

    if case in noLatList:
        npower, ncp, narea = normalizePCA(params, dictPPA)
        if alg == 'sa':
            ppa = npower + ncp + narea
        else:
            ppa = [npower, ncp, narea]
    else:
        npower, nlat, ncp, narea = normalizePLCA(params, dictPPA)
        if alg == 'sa':
            ppa = npower + nlat + ncp + narea
        else:
            ppa = [npower, nlat, ncp, narea]

    return ppa


def runDSE(basic):

    case = basic.case
    alg = basic.alg
    num = basic.num
    params = basic.params
    mode = basic.mode

    # run lhs to pre-sample initial design points
    init_params = basic.paraDict
    dim = len(init_params)
    n_startup_trials = 10
    init_params_arr = pyDOE.lhs(n=dim, samples=n_startup_trials, criterion='maximin')
    init_params_arr = init_params_arr.T
    idx = 0
    for key in init_params:
        init_params[key] = init_params_arr[idx]
        idx += 1

    if encode == 'discrete':
        init_params = map_to_discrete(init_params, params, n_startup_trials)

    # specify the experiment name
    if mode == 'impl':
        study_name = case + "_" + mode + "_dse"
    else:
        study_name = case + "_" + alg + "_dse"
    if parallel:
        # Important: must create the corresponding database in MySQL.
        # Here is the method:
        # mysql -u root -p
        # CREATE DATABASE 'study_name';
        # SHOW DATABASES; (to see if the database is created successfully)
        storage = "mysql+pymysql://root:password@localhost/" + study_name
        print('Using MySQL Database to store the distributed running data!')
    else:
        # Sqlite is not suitable for distributed running.
        storage = "sqlite:///" + study_name + ".db"
        print('Using Sqlite Database to store data!')

    # specify random number seed
    seed = 12345
    # choose the algorithm for DSE
    if alg == "sa":
        print("[INFO] Using Simulated Annealing for HLS DSE")
        sampler = SimulatedAnnealingSampler(seed=seed)
        study = optuna.create_study(storage=storage, study_name=study_name, sampler=sampler, direction="minimize",
                                    load_if_exists=True)
    else:
        if alg == 'motpe_d':
            print("[INFO] Using Discrete Encoding and MOTPE based Bayesian Optimization for HLS DSE")
            n_ei_candidates = 24
            sampler = optuna.samplers.TPESampler(n_startup_trials=n_startup_trials, n_ei_candidates=n_ei_candidates,
                                                 seed=seed)
        elif alg == "motpe_f":
            print("[INFO] Using Float Encoding and MOTPE based Bayesian Optimization for HLS DSE")
            n_ei_candidates = 24
            sampler = optuna.samplers.TPESampler(n_startup_trials=n_startup_trials, n_ei_candidates=n_ei_candidates,
                                                 seed=seed)
        elif alg == "motpe_fl":
            print("[INFO] Using Float Encoding and Latin MOTPE based Bayesian Optimization for HLS DSE")
            from alg.tpe_sampler import TPESampler
            n_ei_candidates = 24
            sampler = TPESampler(n_startup_trials=n_startup_trials, n_ei_candidates=n_ei_candidates,
                                 seed=seed, init_method='lhs', 
                                 init_params=init_params)
        elif alg == "nsga":
            print("[INFO] Using NSGA-II for HLS DSE")
            sampler = optuna.samplers.NSGAIISampler(seed=seed)
        elif alg == "random":  # usually used to collect dataset
            print("[INFO] Using Random Sampling for HLS DSE")
            sampler = optuna.samplers.RandomSampler(seed=seed)
        else:
            print("[INFO] Using Float Encoding and MOTPE based Bayesian Optimization for HLS DSE")
            n_ei_candidates = 24
            sampler = optuna.samplers.TPESampler(n_startup_trials=n_startup_trials, n_ei_candidates=n_ei_candidates,
                                                 seed=seed)

        if case in noLatList:
            study = optuna.create_study(storage=storage, study_name=study_name, sampler=sampler,
                                        directions=["minimize", "minimize", "minimize"], load_if_exists=False)
        else:
            study = optuna.create_study(storage=storage, study_name=study_name, sampler=sampler,
                                        directions=["minimize", "minimize", "minimize", "minimize"],
                                        load_if_exists=False)

    study.optimize(objective, n_trials=num, show_progress_bar=True)
    print("Number of finished trials: ", len(study.trials))

    if alg == "sa":
        optuna.visualization.plot_optimization_history(study)
        optuna.visualization.plot_parallel_coordinate(study)
        optuna.visualization.plot_param_importances(study)
        optuna.visualization.plot_contour(study)
        optuna.visualization.plot_slice(study)

        print("Best trial:")
        print("Value: ", study.best_trial.value)
        print("Params: ")
        for key, value in study.best_trial.params.items():
            print("{}: {}".format(key, value))
    else:
        print("Pareto front:")
        trials = sorted(study.best_trials, key=lambda t: t.values)
        for trial in trials:
            print("Trial#{}".format(trial.number))
            print("Params: {}".format(trial.params))
        print(f"Number of trials on the Pareto front: {len(study.best_trials)}")

        # Visualization
        if case in noLatList:
            trial_with_lowest_power = min(study.best_trials, key=lambda t: t.values[0])
            print(f"Trial with lowest power: ")
            print(f"\tnumber: {trial_with_lowest_power.number}")
            print(f"\tparams: {trial_with_lowest_power.params}")
            print(f"\tvalues: {trial_with_lowest_power.values}")

            trial_with_best_cp = min(study.best_trials, key=lambda t: t.values[1])
            print(f"Trial with best cp: ")
            print(f"\tnumber: {trial_with_best_cp.number}")
            print(f"\tparams: {trial_with_best_cp.params}")
            print(f"\tvalues: {trial_with_best_cp.values}")

            trial_with_smallest_area = min(study.best_trials, key=lambda t: t.values[2])
            print(f"Trial with smallest area: ")
            print(f"\tnumber: {trial_with_smallest_area.number}")
            print(f"\tparams: {trial_with_smallest_area.params}")
            print(f"\tvalues: {trial_with_smallest_area.values}")

            fig_pwr_h = optuna.visualization.plot_optimization_history(study, target=lambda t: t.values[0],
                                                                       target_name="power")
            fig_cp_h = optuna.visualization.plot_optimization_history(study, target=lambda t: t.values[1],
                                                                      target_name="cp")
            fig_area_h = optuna.visualization.plot_optimization_history(study, target=lambda t: t.values[2],
                                                                        target_name="area")
            fig_pwr_h.show()
            fig_cp_h.show()
            fig_area_h.show()

            fig_pwr_i = optuna.visualization.plot_param_importances(study, target=lambda t: t.values[0],
                                                                    target_name="power")
            fig_cp_i = optuna.visualization.plot_param_importances(study, target=lambda t: t.values[1],
                                                                   target_name="cp")
            fig_area_i = optuna.visualization.plot_param_importances(study, target=lambda t: t.values[2],
                                                                     target_name="area")
            fig_pwr_i.show()
            fig_cp_i.show()
            fig_area_i.show()

        else:
            trial_with_lowest_power = min(study.best_trials, key=lambda t: t.values[0])
            print(f"Trial with lowest power: ")
            print(f"\tnumber: {trial_with_lowest_power.number}")
            print(f"\tparams: {trial_with_lowest_power.params}")
            print(f"\tvalues: {trial_with_lowest_power.values}")

            trial_with_best_lat = min(study.best_trials, key=lambda t: t.values[1])
            print(f"Trial with best lat: ")
            print(f"\tnumber: {trial_with_best_lat.number}")
            print(f"\tparams: {trial_with_best_lat.params}")
            print(f"\tvalues: {trial_with_best_lat.values}")

            trial_with_best_cp = min(study.best_trials, key=lambda t: t.values[2])
            print(f"Trial with best cp: ")
            print(f"\tnumber: {trial_with_best_cp.number}")
            print(f"\tparams: {trial_with_best_cp.params}")
            print(f"\tvalues: {trial_with_best_cp.values}")

            trial_with_smallest_area = min(study.best_trials, key=lambda t: t.values[3])
            print(f"Trial with smallest area: ")
            print(f"\tnumber: {trial_with_smallest_area.number}")
            print(f"\tparams: {trial_with_smallest_area.params}")
            print(f"\tvalues: {trial_with_smallest_area.values}")

            fig_pwr_h = optuna.visualization.plot_optimization_history(study, target=lambda t: t.values[0],
                                                                       target_name="power")
            fig_lat_h = optuna.visualization.plot_optimization_history(study, target=lambda t: t.values[1],
                                                                       target_name="lat")
            fig_cp_h = optuna.visualization.plot_optimization_history(study, target=lambda t: t.values[2],
                                                                      target_name="cp")
            fig_area_h = optuna.visualization.plot_optimization_history(study, target=lambda t: t.values[3],
                                                                        target_name="area")
            fig_pwr_h.show()
            fig_lat_h.show()
            fig_cp_h.show()
            fig_area_h.show()

            fig_pwr_i = optuna.visualization.plot_param_importances(study, target=lambda t: t.values[0],
                                                                    target_name="power")
            fig_lat_i = optuna.visualization.plot_param_importances(study, target=lambda t: t.values[1],
                                                                    target_name="lat")
            fig_cp_i = optuna.visualization.plot_param_importances(study, target=lambda t: t.values[2],
                                                                   target_name="cp")
            fig_area_i = optuna.visualization.plot_param_importances(study, target=lambda t: t.values[3],
                                                                     target_name="area")
            fig_pwr_i.show()
            fig_lat_i.show()
            fig_cp_i.show()
            fig_area_i.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HLS Design Space Exploration")
    parser.add_argument("--mode", type=str, help="The running mode of dse flow: hgp, impl.", default="hgp")
    parser.add_argument("--bench", type=str, help="The public benchmark name.", default="MachSuite")
    parser.add_argument("--case", type=str, help="The name of the benchmark.", default="bfs")
    parser.add_argument("--ver", type=str, help="The version of the benchmark.", default="bulk")
    parser.add_argument("--num", type=int, help="The number of optimization iterations.", default=100)
    parser.add_argument("--alg", type=str, help="The DSE algorithm.", default="motpe_fl")
    parser.add_argument("--device", type=str, help="FPGA device for implementation.", default="xc7vx485tffg1761-2")
    parser.add_argument("--clk", type=str, help="Clock period for implementation.", default="10")
    parser.add_argument("--encode", type=str, help="Float or discrete encoding style.", default="float")
    parser.add_argument("--space", type=str, help="Tree-structured or homo-structured design space.", default="tree")
    parser.add_argument("--parallel", type=bool, help="Using parallel running or not.", default=False)
    parser.add_argument("--process", type=int, help="The process number of current running.", default=1)

    args = parser.parse_args()

    mode = args.mode
    bench = args.bench
    case = args.case
    ver = args.ver
    num = args.num
    alg = args.alg
    encode = args.encode
    space = args.space
    parallel = args.parallel
    process = args.process

    root = os.path.abspath("../")
    basic = HLSBasic(root, mode, bench, case, ver, encode, num, alg, space, parallel, process)

    runDSE(basic)

    print("[INFO] HLS Design Space Exploration is Done!")
