import json
from math import floor


def map_to_discrete(paraDict, params, n_start_trials):
    # Call this function when converting lhs samples to options
    inline = params['inline']
    balance = params['balance']
    factor = params['factor']
    arrtype = params['arrtype']
    opimpl = params['opimpl']
    sttype = params['sttype']
    stimpl = params['stimpl']
    stltc = params['stltc']
    opltc = params['opltc']
    state = params['state']

    init_params = paraDict.copy()
    for key in init_params:
        init_params[key] = list()

    # Convert numerical values to actual options
    for sp in range(n_start_trials):
        for key in paraDict:
            name = key.split('_')[0]
            if name == 'FI':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(inline))
                init_params[key].append(inline[idx])
            elif name == 'FB' or name == 'TFB':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(balance))
                init_params[key].append(balance[idx])
            elif name == 'LU':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                init_params[key].append(factor[idx])
            elif name == 'LP':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(state))
                init_params[key].append(state[idx])
            elif name == 'LF':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(state))
                init_params[key].append(state[idx])
            elif name == 'APF':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                init_params[key].append(factor[idx])
            elif name == 'APT':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(arrtype))
                init_params[key].append(arrtype[idx])
            elif name == 'ARF':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                init_params[key].append(factor[idx])
            elif name == 'ART':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(arrtype))
                init_params[key].append(arrtype[idx])
            elif name == 'AST':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(sttype))
                init_params[key].append(sttype[idx])
            elif name == 'ASI':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(stimpl))
                init_params[key].append(stimpl[idx])
            elif name == 'ASL':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(stltc))
                init_params[key].append(stltc[idx])
            elif name == 'IPF':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                init_params[key].append(factor[idx])
            elif name == 'IPT':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(arrtype))
                init_params[key].append(arrtype[idx])
            elif name == 'IRF':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                init_params[key].append(factor[idx])
            elif name == 'IRT':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(arrtype))
                init_params[key].append(arrtype[idx])
            elif name == 'OPI':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opimpl['int']))
                init_params[key].append(opimpl['int'][idx])
            elif name == 'OPL':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opltc))
                init_params[key].append(opltc[idx])
            elif name == 'FOPI':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opimpl['float']))
                init_params[key].append(opimpl['float'][idx])
            elif name == 'FOPL':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opltc))
                init_params[key].append(opltc[idx])
            elif name == 'DOPI':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opimpl['double']))
                init_params[key].append(opimpl['double'][idx])
            elif name == 'DOPL':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opltc))
                init_params[key].append(opltc[idx])
            elif name == 'HOPI':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opimpl['half']))
                init_params[key].append(opimpl['half'][idx])
            elif name == 'HOPL':
                var = paraDict[key][sp]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opltc))
                init_params[key].append(opltc[idx])

    return init_params


def genDirConfig(encode, params, static_config, paraDict, dir_tcl, tempDir, dir_json):
    # Call this function when using tree-structured design space configuration
    top = static_config["top"][0]
    funcList = static_config["funcList"]
    loopList = static_config["loopList"]
    arrList = static_config["arrList"]
    interList = static_config["interList"]
    dictOp = static_config["dictOp"]

    if encode == 'float':
        print("[INFO] Using float encoding method!")
        inline = params['inline']
        balance = params['balance']
        factor = params['factor']
        arrtype = params['arrtype']
        opimpl = params['opimpl']
        sttype = params['sttype']
        stimpl = params['stimpl']
        stltc = params['stltc']
        opltc = params['opltc']
        state = params['state']

        # Convert numerical values to actual options
        for key in paraDict:
            name = key.split('_')[0]
            if name == 'FI':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(inline))
                paraDict[key] = inline[idx]
            elif name == 'FB' or name == 'TFB':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(balance))
                paraDict[key] = balance[idx]
            elif name == 'LU':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                paraDict[key] = factor[idx]
            elif name == 'LP':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(state))
                paraDict[key] = state[idx]
            elif name == 'LF':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(state))
                paraDict[key] = state[idx]
            elif name == 'APF':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                paraDict[key] = factor[idx]
            elif name == 'APT':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(arrtype))
                paraDict[key] = arrtype[idx]
            elif name == 'ARF':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                paraDict[key] = factor[idx]
            elif name == 'ART':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(arrtype))
                paraDict[key] = arrtype[idx]
            elif name == 'AST':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(sttype))
                paraDict[key] = sttype[idx]
            elif name == 'ASI':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(stimpl))
                paraDict[key] = stimpl[idx]
            elif name == 'ASL':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(stltc))
                paraDict[key] = stltc[idx]
            elif name == 'IPF':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                paraDict[key] = factor[idx]
            elif name == 'IPT':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(arrtype))
                paraDict[key] = arrtype[idx]
            elif name == 'IRF':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(factor))
                paraDict[key] = factor[idx]
            elif name == 'IRT':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(arrtype))
                paraDict[key] = arrtype[idx]
            elif name == 'OPI':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opimpl['int']))
                paraDict[key] = opimpl['int'][idx]
            elif name == 'OPL':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opltc))
                paraDict[key] = opltc[idx]
            elif name == 'FOPI':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opimpl['float']))
                paraDict[key] = opimpl['float'][idx]
            elif name == 'FOPL':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opltc))
                paraDict[key] = opltc[idx]
            elif name == 'DOPI':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opimpl['double']))
                paraDict[key] = opimpl['double'][idx]
            elif name == 'DOPL':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opltc))
                paraDict[key] = opltc[idx]
            elif name == 'HOPI':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opimpl['half']))
                paraDict[key] = opimpl['half'][idx]
            elif name == 'HOPL':
                var = paraDict[key]
                assert var < 1.0, "Param value is not less than 1 !"
                idx = floor(var * len(opltc))
                paraDict[key] = opltc[idx]

    else:
        print("[INFO] Using discrete encoding method!")

    # Fill the blanks in dir.json and generate dir.tcl for HLS
    print("[INFO] Generating Vitis HLS directive.tcl file...")
    cntF = cntL = cntA = cntI = cntO = 0
    fileDir = open(dir_tcl, 'w')

    if (paraDict['TFB_0'] == '-on') == 0:
        tcl = "set_directive_expression_balance " + paraDict['TFB_0'] + " " + top
        fileDir.write(tcl + "\n")
    else:
        tcl = "set_directive_expression_balance " + top
        fileDir.write(tcl + "\n")

    for func in funcList:
        if func is None:
            break
        else:
            keyFI = 'FI_' + str(cntF)
            keyFB = 'FB_' + str(cntF)
            tempDir["Function"][func]["INLINE"] = paraDict[keyFI]
            if (paraDict[keyFI] == '-on') == 0:
                tcl = "set_directive_inline " + paraDict[keyFI] + " " + func
                fileDir.write(tcl + "\n")
                tempDir["Function"][func]["BALANCE"] = paraDict[keyFB]
                if (paraDict[keyFB] == '-on') == 0:
                    tcl = "set_directive_expression_balance " + paraDict[keyFB] + " " + func
                    fileDir.write(tcl + "\n")
                else:
                    tcl = "set_directive_expression_balance " + func
                    fileDir.write(tcl + "\n")
            else:
                tcl = "set_directive_inline " + func
                fileDir.write(tcl + "\n")

            cntF = cntF + 1

    for group in loopList:
        ppl_flag = 0
        if group is None:
            break
        else:
            for loop in loopList[group]['level']:
                if ppl_flag == 0:
                    if loop in loopList[group]['flatten']:
                        keyLF = 'LF_' + str(cntL)
                        tempDir["Loop"][group][loop]["FLATTEN"]["-state"] = paraDict[keyLF]
                        if paraDict[keyLF] == '-on':
                            tcl = "set_directive_loop_flatten " + loop
                            fileDir.write(tcl + "\n")
                            cntL = cntL + 1
                            continue
                        else:
                            tcl = "set_directive_loop_flatten -off " + loop
                            fileDir.write(tcl + "\n")
                    if loop in loopList[group]['unroll']:
                        keyLU = 'LU_' + str(cntL)
                        tempDir["Loop"][group][loop]["UNROLL"]["-factor"] = paraDict[keyLU]
                        if paraDict[keyLU] > 0:
                            tcl = "set_directive_unroll -factor " + str(paraDict[keyLU]) + " " + loop
                            fileDir.write(tcl + "\n")
                    if loop in loopList[group]['pipeline']:
                        keyLP = 'LP_' + str(cntL)
                        tempDir["Loop"][group][loop]["PIPELINE"]["-style"] = 'stp'
                        tempDir["Loop"][group][loop]["PIPELINE"]["-state"] = paraDict[keyLP]
                        if paraDict[keyLP] == '-on':
                            tcl = "set_directive_pipeline -style stp " + loop
                            fileDir.write(tcl + "\n")
                            ppl_flag = 1
                        else:
                            tcl = "set_directive_pipeline -off " + loop
                            fileDir.write(tcl + "\n")
                cntL = cntL + 1

    for arr in arrList:
        if arr is None:
            break
        else:
            keyAPF = 'APF_' + str(cntA)
            keyAPT = 'APT_' + str(cntA)
            keyARF = 'ARF_' + str(cntA)
            keyART = 'ART_' + str(cntA)
            keyAST = 'AST_' + str(cntA)
            keyASI = 'ASI_' + str(cntA)
            keyASL = 'ASL_' + str(cntA)
            tempDir["Array"][arr]["PARTITION"]["-factor"] = paraDict[keyAPF]
            tempDir["Array"][arr]["PARTITION"]["-type"] = paraDict[keyAPT]
            tempDir["Array"][arr]["RESHAPE"]["-factor"] = paraDict[keyARF]
            tempDir["Array"][arr]["RESHAPE"]["-type"] = paraDict[keyART]
            tempDir["Array"][arr]["STORAGE"]["-type"] = paraDict[keyAST]
            tempDir["Array"][arr]["STORAGE"]["-impl"] = paraDict[keyASI]
            tempDir["Array"][arr]["STORAGE"]["-latency"] = paraDict[keyASL]
            if paraDict[keyAPF] > 0:
                tcl = "set_directive_array_partition -factor " + str(paraDict[keyAPF]) + " -type " + \
                      paraDict[keyAPT] + " " + arr
                fileDir.write(tcl + "\n")
            if paraDict[keyARF] > 0:
                tcl = "set_directive_array_reshape -factor " + str(paraDict[keyARF]) + " -type " + \
                      paraDict[keyART] + " " + arr
                fileDir.write(tcl + "\n")
            tcl = "set_directive_bind_storage -type " + paraDict[keyAST] + " -impl " + paraDict[keyASI] + \
                  " -latency " + str(paraDict[keyASL]) + " " + arr
            fileDir.write(tcl + "\n")
            cntA = cntA + 1

    for inter in interList:
        if inter is None:
            break
        else:
            keyIPF = 'IPF_' + str(cntI)
            keyIPT = 'IPT_' + str(cntI)
            keyIRF = 'IRF_' + str(cntI)
            keyIRT = 'IRT_' + str(cntI)
            tempDir["Interface"][inter]["PARTITION"]["-factor"] = paraDict[keyIPF]
            tempDir["Interface"][inter]["PARTITION"]["-type"] = paraDict[keyIPT]
            tempDir["Interface"][inter]["RESHAPE"]["-factor"] = paraDict[keyIRF]
            tempDir["Interface"][inter]["RESHAPE"]["-type"] = paraDict[keyIRT]
            if paraDict[keyIPF] > 0:
                tcl = "set_directive_array_partition -factor " + str(paraDict[keyIPF]) + " -type " + \
                      paraDict[keyIPT] + " " + inter
                fileDir.write(tcl + "\n")
            if paraDict[keyIRF] > 0:
                tcl = "set_directive_array_reshape -factor " + str(paraDict[keyIRF]) + " -type " + \
                      paraDict[keyIRT] + " " + inter
                fileDir.write(tcl + "\n")
            cntI = cntI + 1

    for optype in dictOp:
        for key in dictOp[optype]:
            if key is None:
                break
            else:
                opList = dictOp[optype][key]
                for op in opList:
                    if op is None:
                        break
                    else:
                        if optype == 'int':
                            keyOPI = 'OPI_' + str(cntO)
                            keyOPL = 'OPL_' + str(cntO)
                            tempDir["Operation"][key][op]["-impl"] = paraDict[keyOPI]
                            tempDir["Operation"][key][op]["-latency"] = paraDict[keyOPL]
                            tcl = "set_directive_bind_op -op " + op + " -impl " + paraDict[keyOPI] + \
                                  " -latency " + str(paraDict[keyOPL]) + " " + key
                            fileDir.write(tcl + "\n")
                        elif optype == 'float':
                            keyFOPI = 'FOPI_' + str(cntO)
                            keyFOPL = 'FOPL_' + str(cntO)
                            tempDir["Operation"][key][op]["-impl"] = paraDict[keyFOPI]
                            tempDir["Operation"][key][op]["-latency"] = paraDict[keyFOPL]
                            tcl = "set_directive_bind_op -op " + op + " -impl " + paraDict[keyFOPI] + \
                                  " -latency " + str(paraDict[keyFOPL]) + " " + key
                            fileDir.write(tcl + "\n")
                        elif optype == 'double':
                            keyDOPI = 'DOPI_' + str(cntO)
                            keyDOPL = 'DOPL_' + str(cntO)
                            tempDir["Operation"][key][op]["-impl"] = paraDict[keyDOPI]
                            tempDir["Operation"][key][op]["-latency"] = paraDict[keyDOPL]
                            tcl = "set_directive_bind_op -op " + op + " -impl " + paraDict[keyDOPI] + \
                                  " -latency " + str(paraDict[keyDOPL]) + " " + key
                            fileDir.write(tcl + "\n")
                        elif optype == 'half':
                            keyHOPI = 'HOPI_' + str(cntO)
                            keyHOPL = 'HOPL_' + str(cntO)
                            tempDir["Operation"][key][op]["-impl"] = paraDict[keyHOPI]
                            tempDir["Operation"][key][op]["-latency"] = paraDict[keyHOPL]
                            tcl = "set_directive_bind_op -op " + op + " -impl " + paraDict[keyHOPI] + \
                                  " -latency " + str(paraDict[keyHOPL]) + " " + key
                            fileDir.write(tcl + "\n")
                        cntO = cntO + 1

    fileDir.close()

    with open(dir_json, "w") as fout:
        fout.write(json.dumps(tempDir, indent=4))

    print("[INFO] Successfully generated Vitis HLS directive.tcl and hls.tcl files !")
