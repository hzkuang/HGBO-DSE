open_project md_prj

add_files md.c
add_files input.data
add_files check.data
add_files local_support.c

add_files -tb ../../common/support.c
add_files -tb ../../common/harness.c 

set_top md_kernel
open_solution -reset solution

set_part xc7vx485tffg1761-2
create_clock -period 10

csynth_design
# cosim_design -rtl verilog -tool xsim
export_design -flow impl -rtl verilog -format ip_catalog

exit
