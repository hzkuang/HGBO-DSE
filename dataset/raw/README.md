## Raw HLS Dataset
Available at https://pan.baidu.com/s/12rG1JeOh0VKh-UVotlaWQw. (Extraction code: vuuw)

This dataset contains 10 sub-datasets with over 10,000 samples. 
Each sub-dataset has over 1,000 samples.

For each sample prj_*, we collect 4-level files:
- Tcl scripts (/prj_*/script/)
    - hls.tcl (the synthesis script)
    - dir.tcl (stores the directives)
- IR files (/prj_*/graph/)
    - adb (to construct CDFG)
    - adb.xml (FSMD model)
    - a.o.3.bc (IR code)
- HLS reports (/prj_\*/report/) and the generated Verilog codes (/prj_\*/verilog)
    - *_csynth.rpt (post-HLS)
- Post-implementation reports (/prj_*/report/)
    - export_syn.rpt (post-synthesis)
    - export_impl.rpt (post-implementation)

Note that users can use this raw dataset to fit their own ML models conveniently.
