open_project viterbi_prj

add_files viterbi.c
add_files input.data
add_files check.data
add_files local_support.c

add_files -tb ../../common/support.c
add_files -tb ../../common/harness.c 

set_top viterbi
open_solution -reset solution

set_part xc7vx485tffg1761-2
create_clock -period 10

csynth_design
# cosim_design -rtl verilog -tool xsim
export_design -flow impl -rtl verilog -format ip_catalog

exit
