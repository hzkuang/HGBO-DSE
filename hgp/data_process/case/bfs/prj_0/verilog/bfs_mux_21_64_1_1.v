// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2022.1 (64-bit)
// Tool Version Limit: 2022.04
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// ==============================================================

`timescale 1ns/1ps

module bfs_mux_21_64_1_1 #(
parameter
    ID                = 0,
    NUM_STAGE         = 1,
    din0_WIDTH       = 32,
    din1_WIDTH       = 32,
    din2_WIDTH         = 32,
    dout_WIDTH            = 32
)(
    input  [63 : 0]     din0,
    input  [63 : 0]     din1,
    input  [0 : 0]    din2,
    output [63 : 0]   dout);

// puts internal signals
wire [0 : 0]     sel;
// level 1 signals
wire [63 : 0]         mux_1_0;

assign sel = din2;

// Generate level 1 logic
assign mux_1_0 = (sel[0] == 0)? din0 : din1;

// output logic
assign dout = mux_1_0;

endmodule
