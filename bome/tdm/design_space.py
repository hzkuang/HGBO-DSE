

def basicOption():
    return {
        "INLINE": {"-on": [], "-off": [], "-recursive": []},
        "BALANCE": {"-on": [], "-off": []},
        "FLATTEN": {"-on": [], "-off": []},
        "PIPELINE": {"-style": []},
        "UNROLL": {"-factor": []},
        "PARTITION": {"-factor": [], "-type": []},
        "RESHAPE": {"-factor": [], "-type": []},
        "STORAGE": {"-type": [], "-impl": [], "-latency": []},
    }


def config_tree_space(static_config, encode, trial, params):
    # Call this function to construct tree-structured design space,
    # which can remove the invalid configurations.
    print("[INFO] Configuring tree-structured design space...")
    tempDir = {"Option": basicOption(), "Function": {}, "Loop": {}, "Array": {}, "Interface": {}, "Operation": {}}

    # top = static_config["top"][0]
    funcList = static_config["funcList"]
    loopList = static_config["loopList"]
    arrList = static_config["arrList"]
    interList = static_config["interList"]
    dictOp = static_config["dictOp"]

    paraFunc = {}
    paraLoop = {}
    paraArr = {}
    paraInter = {}
    paraOp = {}
    paraDict = {}

    cntF = cntL = cntA = cntI = cntO = 0

    if encode == 'float':
        paraFunc.update({'TFB_0': trial.suggest_float('TFB_0', 0.0, 1.0)})
    elif encode == 'discrete':
        paraFunc.update({'TFB_0': trial.suggest_categorical('TFB_0', params['balance'])})

    for func in funcList:
        if func is None:
            break
        else:
            dictFunc = {
                func: {
                    "INLINE": [],
                    "BALANCE": []
                }
            }
            tempDir["Function"].update(dictFunc)
            keyFI = 'FI_' + str(cntF)
            keyFB = 'FB_' + str(cntF)
            if encode == 'float':
                paraFunc.update({keyFI: trial.suggest_float(keyFI, 0.0, 1.0)})
                if paraFunc[keyFI] < 0.5:
                    pass
                else:
                    paraFunc.update({keyFB: trial.suggest_float(keyFB, 0.0, 1.0)})
            elif encode == 'discrete':
                paraFunc.update({keyFI: trial.suggest_categorical(keyFI, params['inline'])})
                if paraFunc[keyFI] == '-off':
                    paraFunc.update({keyFB: trial.suggest_categorical(keyFB, params['balance'])})
            cntF = cntF + 1
    paraDict.update(paraFunc)

    for group in loopList:
        ppl_flag = 0
        if group is None:
            break
        else:
            for loop in loopList[group]['level']:
                dictLoop = {
                    loop: {}
                }
                if ppl_flag == 0:
                    if loop in loopList[group]['flatten']:
                        flt = {
                            "FLATTEN": {
                                "-state": []
                            }
                        }
                        dictLoop[loop].update(flt)
                        keyLF = 'LF_' + str(cntL)
                        if encode == 'float':
                            paraLoop.update({keyLF: trial.suggest_float(keyLF, 0.0, 1.0)})
                            if paraLoop[keyLF] < 0.5:
                                cntL = cntL + 1
                                continue
                        elif encode == 'discrete':
                            paraLoop.update({keyLF: trial.suggest_categorical(keyLF, params['state'])})
                            if paraLoop[keyLF] == '-on':
                                cntL = cntL + 1
                                continue
                    if loop in loopList[group]['unroll']:
                        unroll = {
                            "UNROLL": {
                                "-factor": []
                            }
                        }
                        dictLoop[loop].update(unroll)
                        keyLU = 'LU_' + str(cntL)
                        if encode == 'float':
                            paraLoop.update({keyLU: trial.suggest_float(keyLU, 0.0, 1.0)})
                        elif encode == 'discrete':
                            paraLoop.update({keyLU: trial.suggest_categorical(keyLU, params['factor'])})
                    if loop in loopList[group]['pipeline']:
                        ppl = {
                            "PIPELINE": {
                                "-style": [],
                                "-state": []
                            }
                        }
                        dictLoop[loop].update(ppl)
                        keyLP = 'LP_' + str(cntL)
                        if encode == 'float':
                            paraLoop.update({keyLP: trial.suggest_float(keyLP, 0.0, 1.0)})
                            if paraLoop[keyLP] < 0.5:
                                ppl_flag = 1
                        elif encode == 'discrete':
                            paraLoop.update({keyLP: trial.suggest_categorical(keyLP, params['state'])})
                            if paraLoop[keyLP] == '-on':
                                ppl_flag = 1

                cntL = cntL + 1
                loopList[group].update(dictLoop)
    tempDir["Loop"].update(loopList)
    paraDict.update(paraLoop)

    for arr in arrList:
        if arr is None:
            break
        else:
            dictArr = {
                arr: {
                    "PARTITION": {
                        "-factor": [],
                        "-type": []},
                    "RESHAPE": {
                        "-factor": [],
                        "-type": []},
                    "STORAGE": {
                        "-type": [],
                        "-impl": [],
                        "-latency": []},
                }
            }
            tempDir["Array"].update(dictArr)
            keyAPF = 'APF_' + str(cntA)
            keyAPT = 'APT_' + str(cntA)
            keyARF = 'ARF_' + str(cntA)
            keyART = 'ART_' + str(cntA)
            keyAST = 'AST_' + str(cntA)
            keyASI = 'ASI_' + str(cntA)
            keyASL = 'ASL_' + str(cntA)
            if encode == 'float':
                paraArr.update({keyAPF: trial.suggest_float(keyAPF, 0.0, 1.0)})
                paraArr.update({keyAPT: trial.suggest_float(keyAPT, 0.0, 1.0)})
                paraArr.update({keyARF: trial.suggest_float(keyARF, 0.0, 1.0)})
                paraArr.update({keyART: trial.suggest_float(keyART, 0.0, 1.0)})
                paraArr.update({keyAST: trial.suggest_float(keyAST, 0.0, 1.0)})
                paraArr.update({keyASI: trial.suggest_float(keyASI, 0.0, 1.0)})
                paraArr.update({keyASL: trial.suggest_float(keyASL, 0.0, 1.0)})
            elif encode == 'discrete':
                paraArr.update({keyAPF: trial.suggest_categorical(keyAPF, params['factor'])})
                paraArr.update({keyAPT: trial.suggest_categorical(keyAPT, params['arrtype'])})
                paraArr.update({keyARF: trial.suggest_categorical(keyARF, params['factor'])})
                paraArr.update({keyART: trial.suggest_categorical(keyART, params['arrtype'])})
                paraArr.update({keyAST: trial.suggest_categorical(keyAST, params['sttype'])})
                paraArr.update({keyASI: trial.suggest_categorical(keyASI, params['stimpl'])})
                paraArr.update({keyASL: trial.suggest_categorical(keyASL, params['stltc'])})

            cntA = cntA + 1
    paraDict.update(paraArr)

    for inter in interList:
        if inter is None:
            break
        else:
            dictInter = {
                inter: {
                    "PARTITION": {
                        "-factor": [],
                        "-type": []},
                    "RESHAPE": {
                        "-factor": [],
                        "-type": []},
                }
            }
            tempDir["Interface"].update(dictInter)
            keyIPF = 'IPF_' + str(cntI)
            keyIPT = 'IPT_' + str(cntI)
            keyIRF = 'IRF_' + str(cntI)
            keyIRT = 'IRT_' + str(cntI)
            if encode == 'float':
                paraInter.update({keyIPF: trial.suggest_float(keyIPF, 0.0, 1.0)})
                paraInter.update({keyIPT: trial.suggest_float(keyIPT, 0.0, 1.0)})
                paraInter.update({keyIRF: trial.suggest_float(keyIRF, 0.0, 1.0)})
                paraInter.update({keyIRT: trial.suggest_float(keyIRT, 0.0, 1.0)})
            elif encode == 'discrete':
                paraInter.update({keyIPF: trial.suggest_categorical(keyIPF, params['factor'])})
                paraInter.update({keyIPT: trial.suggest_categorical(keyIPT, params['arrtype'])})
                paraInter.update({keyIRF: trial.suggest_categorical(keyIRF, params['factor'])})
                paraInter.update({keyIRT: trial.suggest_categorical(keyIRT, params['arrtype'])})

            cntI = cntI + 1
    paraDict.update(paraInter)

    for optype in dictOp:
        for key in dictOp[optype]:
            if key is None:
                break
            else:
                tempDir["Operation"].update({key: {}})
                opList = dictOp[optype][key]
                for op in opList:
                    if op is None:
                        break
                    else:
                        itemOp = {
                            op: {
                                "-impl": [],
                                "-latency": []
                            }
                        }
                        tempDir["Operation"][key].update(itemOp)
                        if encode == 'float':
                            if optype == 'int':
                                keyOPI = 'OPI_' + str(cntO)
                                keyOPL = 'OPL_' + str(cntO)
                                paraOp.update({keyOPI: trial.suggest_float(keyOPI, 0.0, 1.0)})
                                paraOp.update({keyOPL: trial.suggest_float(keyOPL, 0.0, 1.0)})
                            elif optype == 'float':
                                keyFOPI = 'FOPI_' + str(cntO)
                                keyFOPL = 'FOPL_' + str(cntO)
                                paraOp.update({keyFOPI: trial.suggest_float(keyFOPI, 0.0, 1.0)})
                                paraOp.update({keyFOPL: trial.suggest_float(keyFOPL, 0.0, 1.0)})
                            elif optype == 'double':
                                keyDOPI = 'DOPI_' + str(cntO)
                                keyDOPL = 'DOPL_' + str(cntO)
                                paraOp.update({keyDOPI: trial.suggest_float(keyDOPI, 0.0, 1.0)})
                                paraOp.update({keyDOPL: trial.suggest_float(keyDOPL, 0.0, 1.0)})
                            elif optype == 'half':
                                keyHOPI = 'HOPI_' + str(cntO)
                                keyHOPL = 'HOPL_' + str(cntO)
                                paraOp.update({keyHOPI: trial.suggest_float(keyHOPI, 0.0, 1.0)})
                                paraOp.update({keyHOPL: trial.suggest_float(keyHOPL, 0.0, 1.0)})
                        elif encode == 'discrete':
                            if optype == 'int':
                                keyOPI = 'OPI_' + str(cntO)
                                keyOPL = 'OPL_' + str(cntO)
                                paraOp.update({keyOPI: trial.suggest_categorical(keyOPI, params['opimpl']['int'])})
                                paraOp.update({keyOPL: trial.suggest_categorical(keyOPL, params['opltc'])})
                            elif optype == 'float':
                                keyFOPI = 'FOPI_' + str(cntO)
                                keyFOPL = 'FOPL_' + str(cntO)
                                paraOp.update({keyFOPI: trial.suggest_categorical(keyFOPI, params['opimpl']['float'])})
                                paraOp.update({keyFOPL: trial.suggest_categorical(keyFOPL, params['opltc'])})
                            elif optype == 'double':
                                keyDOPI = 'DOPI_' + str(cntO)
                                keyDOPL = 'DOPL_' + str(cntO)
                                paraOp.update({keyDOPI: trial.suggest_categorical(keyDOPI, params['opimpl']['double'])})
                                paraOp.update({keyDOPL: trial.suggest_categorical(keyDOPL, params['opltc'])})
                            elif optype == 'half':
                                keyHOPI = 'HOPI_' + str(cntO)
                                keyHOPL = 'HOPL_' + str(cntO)
                                paraOp.update({keyHOPI: trial.suggest_categorical(keyHOPI, params['opimpl']['half'])})
                                paraOp.update({keyHOPL: trial.suggest_categorical(keyHOPL, params['opltc'])})

                        cntO = cntO + 1
    paraDict.update(paraOp)

    print("[INFO] Total parameters: " + str(len(paraDict)))
    print("[INFO] Design space configuration done!")

    return tempDir, paraDict


def floatParaSpace(trial, paraDict, fromVal: float = 0.0, toVal: float = 1.0):
    # Call this function to configure homogeneous design space using float distributions.
    for key in paraDict:
        paraDict[key] = trial.suggest_float(key, fromVal, toVal)
    return paraDict


def discreteParaSpace(trial, paraDict, params):
    # Call this function to configure homogeneous design space using discrete distributions.
    for key in paraDict:
        tag = key.split('_')[0]
        if tag == 'FI':
            paraDict[key] = trial.suggest_categorical(key, params['inline'])
        elif tag == 'FB' or tag == 'TFB':
            paraDict[key] = trial.suggest_categorical(key, params['balance'])
        elif tag == 'LU':
            paraDict[key] = trial.suggest_categorical(key, params['factor'])
        elif (tag == 'LP') or (tag == 'LF'):
            paraDict[key] = trial.suggest_categorical(key, params['state'])
        elif (tag == 'IPF') or (tag == 'IRF') or (tag == 'APF') or (tag == 'ARF'):
            paraDict[key] = trial.suggest_categorical(key, params['factor'])
        elif (tag == 'IPT') or (tag == 'IRT') or (tag == 'APT') or (tag == 'ART'):
            paraDict[key] = trial.suggest_categorical(key, params['arrtype'])
        elif tag == 'AST':
            paraDict[key] = trial.suggest_categorical(key, params['sttype'])
        elif tag == 'ASI':
            paraDict[key] = trial.suggest_categorical(key, params['stimpl'])
        elif tag == 'OPI':
            paraDict[key] = trial.suggest_categorical(key, params['opimpl']['int'])
        elif tag == 'FOPI':
            paraDict[key] = trial.suggest_categorical(key, params['opimpl']['float'])
        elif tag == 'DOPI':
            paraDict[key] = trial.suggest_categorical(key, params['opimpl']['double'])
        elif tag == 'HOPI':
            paraDict[key] = trial.suggest_categorical(key, params['opimpl']['half'])
        elif tag == 'ASL':
            paraDict[key] = trial.suggest_categorical(key, params['stltc'])
        elif (tag == 'OPL') or (tag == 'FOPL') or (tag == 'DOPL') or (tag == 'HOPL'):
            paraDict[key] = trial.suggest_categorical(key, params['opltc'])
        else:
            print("[WARNING] No corresponding parameter type!!!")

    return paraDict
