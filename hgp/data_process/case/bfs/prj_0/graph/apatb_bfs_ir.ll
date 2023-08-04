; ModuleID = '/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk/bfs_random_prj/solution/.autopilot/db/a.g.ld.5.gdce.bc'
source_filename = "llvm-link"
target datalayout = "e-m:e-i64:64-i128:128-i256:256-i512:512-i1024:1024-i2048:2048-i4096:4096-n8:16:32:64-S128-v16:16-v24:32-v32:32-v48:64-v96:128-v192:256-v256:256-v512:512-v1024:1024"
target triple = "fpga64-xilinx-none"

%struct.node_t_struct = type { i64, i64 }
%struct.edge_t_struct = type { i64 }

; Function Attrs: inaccessiblememonly nounwind
declare void @llvm.sideeffect() #0

; Function Attrs: noinline
define void @apatb_bfs_ir(%struct.node_t_struct* noalias nocapture nonnull readonly "fpga.decayed.dim.hint"="256" %nodes, %struct.edge_t_struct* noalias nocapture nonnull readonly "fpga.decayed.dim.hint"="4096" %edges, i64 %starting_node, i8* noalias nocapture nonnull "fpga.decayed.dim.hint"="256" %level, i64* noalias nocapture nonnull "fpga.decayed.dim.hint"="10" %level_counts) local_unnamed_addr #1 {
entry:
  %malloccall = call i8* @malloc(i64 4096)
  %nodes_copy = bitcast i8* %malloccall to [256 x i128]*
  %malloccall1_0 = call i8* @malloc(i64 16384)
  %edges_copy_0 = bitcast i8* %malloccall1_0 to [2048 x i64]*
  %malloccall1_1 = call i8* @malloc(i64 16384)
  %edges_copy_1 = bitcast i8* %malloccall1_1 to [2048 x i64]*
  %level_copy = alloca [256 x i8], align 512
  %level_counts_copy_0 = alloca [5 x i64], align 512
  %level_counts_copy_1 = alloca [5 x i64], align 512
  %0 = bitcast %struct.node_t_struct* %nodes to [256 x %struct.node_t_struct]*
  %1 = bitcast %struct.edge_t_struct* %edges to [4096 x %struct.edge_t_struct]*
  %2 = bitcast i8* %level to [256 x i8]*
  %3 = bitcast i64* %level_counts to [10 x i64]*
  call void @copy_in([256 x %struct.node_t_struct]* nonnull %0, [256 x i128]* %nodes_copy, [4096 x %struct.edge_t_struct]* nonnull %1, [2048 x i64]* %edges_copy_0, [2048 x i64]* %edges_copy_1, [256 x i8]* nonnull %2, [256 x i8]* nonnull align 512 %level_copy, [10 x i64]* nonnull %3, [5 x i64]* nonnull align 512 %level_counts_copy_0, [5 x i64]* nonnull align 512 %level_counts_copy_1)
  %4 = getelementptr [256 x i128], [256 x i128]* %nodes_copy, i32 0, i32 0
  %5 = getelementptr [2048 x i64], [2048 x i64]* %edges_copy_0, i32 0, i32 0
  %6 = getelementptr [2048 x i64], [2048 x i64]* %edges_copy_1, i32 0, i32 0
  %7 = getelementptr inbounds [256 x i8], [256 x i8]* %level_copy, i32 0, i32 0
  %level_counts_copy.gep_0 = getelementptr [5 x i64], [5 x i64]* %level_counts_copy_0, i64 0, i32 0
  %level_counts_copy.gep_1 = getelementptr [5 x i64], [5 x i64]* %level_counts_copy_1, i64 0, i32 0
  call void @llvm.sideeffect() #0 [ "xlx_array_partition"(i64* %5, i32 0, i32 1, i32 0, i1 false) ], !dbg !5
  call void @llvm.sideeffect() #0 [ "xlx_array_partition"(i64* %6, i32 0, i32 1, i32 0, i1 false) ], !dbg !5
  call void @llvm.sideeffect() #0 [ "xlx_array_partition"(i64* %level_counts_copy.gep_0, i32 0, i32 1, i32 0, i1 false) ], !dbg !40
  call void @llvm.sideeffect() #0 [ "xlx_array_partition"(i64* %level_counts_copy.gep_1, i32 0, i32 1, i32 0, i1 false) ], !dbg !40
  call void @apatb_bfs_hw(i128* %4, [2048 x i64]* %edges_copy_0, [2048 x i64]* %edges_copy_1, i64 %starting_node, i8* %7, [5 x i64]* %level_counts_copy_0, [5 x i64]* %level_counts_copy_1)
  call void @copy_back([256 x %struct.node_t_struct]* %0, [256 x i128]* %nodes_copy, [4096 x %struct.edge_t_struct]* %1, [2048 x i64]* %edges_copy_0, [2048 x i64]* %edges_copy_1, [256 x i8]* %2, [256 x i8]* %level_copy, [10 x i64]* %3, [5 x i64]* %level_counts_copy_0, [5 x i64]* %level_counts_copy_1)
  call void @free(i8* %malloccall)
  call void @free(i8* %malloccall1_0)
  call void @free(i8* %malloccall1_1)
  ret void
}

declare noalias i8* @malloc(i64) local_unnamed_addr

; Function Attrs: argmemonly noinline norecurse
define internal fastcc void @onebyonecpy_hls.p0a256struct.node_t_struct([256 x i128]* noalias, [256 x %struct.node_t_struct]* noalias readonly) unnamed_addr #2 {
entry:
  %2 = icmp eq [256 x i128]* %0, null
  %3 = icmp eq [256 x %struct.node_t_struct]* %1, null
  %4 = or i1 %2, %3
  br i1 %4, label %ret, label %copy

copy:                                             ; preds = %entry
  br label %for.loop

for.loop:                                         ; preds = %for.loop, %copy
  %for.loop.idx5 = phi i64 [ 0, %copy ], [ %for.loop.idx.next, %for.loop ]
  %src.addr.01 = getelementptr [256 x %struct.node_t_struct], [256 x %struct.node_t_struct]* %1, i64 0, i64 %for.loop.idx5, i32 0
  %5 = getelementptr [256 x i128], [256 x i128]* %0, i64 0, i64 %for.loop.idx5
  %6 = load i64, i64* %src.addr.01, align 8
  %7 = zext i64 %6 to i128
  %src.addr.13 = getelementptr [256 x %struct.node_t_struct], [256 x %struct.node_t_struct]* %1, i64 0, i64 %for.loop.idx5, i32 1
  %8 = load i64, i64* %src.addr.13, align 8
  %9 = zext i64 %8 to i128
  %10 = shl i128 %9, 64
  %.partset = or i128 %10, %7
  store i128 %.partset, i128* %5, align 8
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx5, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, 256
  br i1 %exitcond, label %for.loop, label %ret

ret:                                              ; preds = %for.loop, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse
define internal fastcc void @onebyonecpy_hls.p0a256i8([256 x i8]* noalias align 512, [256 x i8]* noalias readonly) unnamed_addr #2 {
entry:
  %2 = icmp eq [256 x i8]* %0, null
  %3 = icmp eq [256 x i8]* %1, null
  %4 = or i1 %2, %3
  br i1 %4, label %ret, label %copy

copy:                                             ; preds = %entry
  br label %for.loop

for.loop:                                         ; preds = %for.loop, %copy
  %for.loop.idx1 = phi i64 [ 0, %copy ], [ %for.loop.idx.next, %for.loop ]
  %dst.addr = getelementptr [256 x i8], [256 x i8]* %0, i64 0, i64 %for.loop.idx1
  %src.addr = getelementptr [256 x i8], [256 x i8]* %1, i64 0, i64 %for.loop.idx1
  %5 = load i8, i8* %src.addr, align 1
  store i8 %5, i8* %dst.addr, align 1
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx1, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, 256
  br i1 %exitcond, label %for.loop, label %ret

ret:                                              ; preds = %for.loop, %entry
  ret void
}

declare void @free(i8*) local_unnamed_addr

; Function Attrs: nounwind
declare void @llvm.assume(i1) #3

; Function Attrs: argmemonly noinline norecurse
define internal void @onebyonecpy_hls.p0a4096struct.edge_t_struct.3.4([2048 x i64]* noalias "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="0" %_0, [2048 x i64]* noalias "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="0" %_1, [4096 x %struct.edge_t_struct]* noalias readonly "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="1") #2 {
entry:
  %1 = icmp eq [2048 x i64]* %_0, null
  %2 = icmp eq [4096 x %struct.edge_t_struct]* %0, null
  %3 = or i1 %1, %2
  br i1 %3, label %ret, label %copy

copy:                                             ; preds = %entry
  br label %for.loop

for.loop:                                         ; preds = %dst.addr.02.exit, %copy
  %for.loop.idx3 = phi i64 [ 0, %copy ], [ %for.loop.idx.next, %dst.addr.02.exit ]
  %src.addr.01 = getelementptr [4096 x %struct.edge_t_struct], [4096 x %struct.edge_t_struct]* %0, i64 0, i64 %for.loop.idx3, i32 0
  %4 = urem i64 %for.loop.idx3, 2
  %5 = udiv i64 %for.loop.idx3, 2
  %6 = getelementptr [2048 x i64], [2048 x i64]* %_0, i64 0, i64 %5
  %7 = getelementptr [2048 x i64], [2048 x i64]* %_1, i64 0, i64 %5
  %8 = load i64, i64* %src.addr.01, align 8
  %9 = trunc i64 %4 to i1
  %cond = icmp eq i1 %9, false
  br i1 %cond, label %dst.addr.02.case.0, label %dst.addr.02.case.1

dst.addr.02.case.0:                               ; preds = %for.loop
  store i64 %8, i64* %6, align 8
  br label %dst.addr.02.exit

dst.addr.02.case.1:                               ; preds = %for.loop
  call void @llvm.assume(i1 %9)
  store i64 %8, i64* %7, align 8
  br label %dst.addr.02.exit

dst.addr.02.exit:                                 ; preds = %dst.addr.02.case.1, %dst.addr.02.case.0
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx3, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, 4096
  br i1 %exitcond, label %for.loop, label %ret

ret:                                              ; preds = %dst.addr.02.exit, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse
define internal void @onebyonecpy_hls.p0a10i64.5.6([5 x i64]* noalias align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="0" %_0, [5 x i64]* noalias align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="0" %_1, [10 x i64]* noalias readonly "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="1") #2 {
entry:
  %1 = icmp eq [5 x i64]* %_0, null
  %2 = icmp eq [10 x i64]* %0, null
  %3 = or i1 %1, %2
  br i1 %3, label %ret, label %copy

copy:                                             ; preds = %entry
  br label %for.loop

for.loop:                                         ; preds = %dst.addr.exit, %copy
  %for.loop.idx1 = phi i64 [ 0, %copy ], [ %for.loop.idx.next, %dst.addr.exit ]
  %4 = urem i64 %for.loop.idx1, 2
  %5 = udiv i64 %for.loop.idx1, 2
  %dst.addr_0 = getelementptr [5 x i64], [5 x i64]* %_0, i64 0, i64 %5
  %dst.addr_1 = getelementptr [5 x i64], [5 x i64]* %_1, i64 0, i64 %5
  %src.addr = getelementptr [10 x i64], [10 x i64]* %0, i64 0, i64 %for.loop.idx1
  %6 = load i64, i64* %src.addr, align 8
  %7 = trunc i64 %4 to i1
  %cond = icmp eq i1 %7, false
  br i1 %cond, label %dst.addr.case.0, label %dst.addr.case.1

dst.addr.case.0:                                  ; preds = %for.loop
  store i64 %6, i64* %dst.addr_0, align 8
  br label %dst.addr.exit

dst.addr.case.1:                                  ; preds = %for.loop
  call void @llvm.assume(i1 %7)
  store i64 %6, i64* %dst.addr_1, align 8
  br label %dst.addr.exit

dst.addr.exit:                                    ; preds = %dst.addr.case.1, %dst.addr.case.0
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx1, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, 10
  br i1 %exitcond, label %for.loop, label %ret

ret:                                              ; preds = %dst.addr.exit, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse
define internal void @copy_in([256 x %struct.node_t_struct]* noalias readonly "orig.arg.no"="0", [256 x i128]* noalias "orig.arg.no"="1", [4096 x %struct.edge_t_struct]* noalias readonly "orig.arg.no"="2", [2048 x i64]* noalias "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="3" %_0, [2048 x i64]* noalias "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="3" %_1, [256 x i8]* noalias readonly "orig.arg.no"="4", [256 x i8]* noalias align 512 "orig.arg.no"="5", [10 x i64]* noalias readonly "orig.arg.no"="6", [5 x i64]* noalias align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="7" %_01, [5 x i64]* noalias align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="7" %_12) #4 {
entry:
  call fastcc void @onebyonecpy_hls.p0a256struct.node_t_struct([256 x i128]* %1, [256 x %struct.node_t_struct]* %0)
  call void @onebyonecpy_hls.p0a4096struct.edge_t_struct.3.4([2048 x i64]* %_0, [2048 x i64]* %_1, [4096 x %struct.edge_t_struct]* %2)
  call fastcc void @onebyonecpy_hls.p0a256i8([256 x i8]* align 512 %4, [256 x i8]* %3)
  call void @onebyonecpy_hls.p0a10i64.5.6([5 x i64]* align 512 %_01, [5 x i64]* align 512 %_12, [10 x i64]* %5)
  ret void
}

; Function Attrs: argmemonly noinline norecurse
define internal void @onebyonecpy_hls.p0a4096struct.edge_t_struct.11.12([4096 x %struct.edge_t_struct]* noalias "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="0", [2048 x i64]* noalias readonly "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="1" %_0, [2048 x i64]* noalias readonly "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="1" %_1) #2 {
entry:
  %1 = icmp eq [4096 x %struct.edge_t_struct]* %0, null
  %2 = icmp eq [2048 x i64]* %_0, null
  %3 = or i1 %1, %2
  br i1 %3, label %ret, label %copy

copy:                                             ; preds = %entry
  br label %for.loop

for.loop:                                         ; preds = %src.addr.01.exit, %copy
  %for.loop.idx3 = phi i64 [ 0, %copy ], [ %for.loop.idx.next, %src.addr.01.exit ]
  %4 = urem i64 %for.loop.idx3, 2
  %5 = udiv i64 %for.loop.idx3, 2
  %6 = getelementptr [2048 x i64], [2048 x i64]* %_0, i64 0, i64 %5
  %7 = getelementptr [2048 x i64], [2048 x i64]* %_1, i64 0, i64 %5
  %dst.addr.02 = getelementptr [4096 x %struct.edge_t_struct], [4096 x %struct.edge_t_struct]* %0, i64 0, i64 %for.loop.idx3, i32 0
  %8 = trunc i64 %4 to i1
  %cond = icmp eq i1 %8, false
  br i1 %cond, label %src.addr.01.case.0, label %src.addr.01.case.1

src.addr.01.case.0:                               ; preds = %for.loop
  %9 = load i64, i64* %6, align 8
  br label %src.addr.01.exit

src.addr.01.case.1:                               ; preds = %for.loop
  call void @llvm.assume(i1 %8)
  %10 = load i64, i64* %7, align 8
  br label %src.addr.01.exit

src.addr.01.exit:                                 ; preds = %src.addr.01.case.1, %src.addr.01.case.0
  %11 = phi i64 [ %9, %src.addr.01.case.0 ], [ %10, %src.addr.01.case.1 ]
  store i64 %11, i64* %dst.addr.02, align 8
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx3, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, 4096
  br i1 %exitcond, label %for.loop, label %ret

ret:                                              ; preds = %src.addr.01.exit, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse
define internal void @onebyonecpy_hls.p0a10i64.13.14([10 x i64]* noalias "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="0", [5 x i64]* noalias readonly align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="1" %_0, [5 x i64]* noalias readonly align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="1" %_1) #2 {
entry:
  %1 = icmp eq [10 x i64]* %0, null
  %2 = icmp eq [5 x i64]* %_0, null
  %3 = or i1 %1, %2
  br i1 %3, label %ret, label %copy

copy:                                             ; preds = %entry
  br label %for.loop

for.loop:                                         ; preds = %src.addr.exit, %copy
  %for.loop.idx1 = phi i64 [ 0, %copy ], [ %for.loop.idx.next, %src.addr.exit ]
  %dst.addr = getelementptr [10 x i64], [10 x i64]* %0, i64 0, i64 %for.loop.idx1
  %4 = urem i64 %for.loop.idx1, 2
  %5 = udiv i64 %for.loop.idx1, 2
  %src.addr_0 = getelementptr [5 x i64], [5 x i64]* %_0, i64 0, i64 %5
  %src.addr_1 = getelementptr [5 x i64], [5 x i64]* %_1, i64 0, i64 %5
  %6 = trunc i64 %4 to i1
  %cond = icmp eq i1 %6, false
  br i1 %cond, label %src.addr.case.0, label %src.addr.case.1

src.addr.case.0:                                  ; preds = %for.loop
  %_01 = load i64, i64* %src.addr_0, align 8
  br label %src.addr.exit

src.addr.case.1:                                  ; preds = %for.loop
  call void @llvm.assume(i1 %6)
  %_12 = load i64, i64* %src.addr_1, align 8
  br label %src.addr.exit

src.addr.exit:                                    ; preds = %src.addr.case.1, %src.addr.case.0
  %7 = phi i64 [ %_01, %src.addr.case.0 ], [ %_12, %src.addr.case.1 ]
  store i64 %7, i64* %dst.addr, align 8
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx1, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, 10
  br i1 %exitcond, label %for.loop, label %ret

ret:                                              ; preds = %src.addr.exit, %entry
  ret void
}

; Function Attrs: argmemonly noinline norecurse
define internal void @copy_out([256 x %struct.node_t_struct]* noalias "orig.arg.no"="0", [256 x i128]* noalias readonly "orig.arg.no"="1", [4096 x %struct.edge_t_struct]* noalias "orig.arg.no"="2", [2048 x i64]* noalias readonly "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="3" %_0, [2048 x i64]* noalias readonly "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="3" %_1, [256 x i8]* noalias "orig.arg.no"="4", [256 x i8]* noalias readonly align 512 "orig.arg.no"="5", [10 x i64]* noalias "orig.arg.no"="6", [5 x i64]* noalias readonly align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="7" %_01, [5 x i64]* noalias readonly align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="7" %_12) #5 {
entry:
  call fastcc void @onebyonecpy_hls.p0a256struct.node_t_struct.29([256 x %struct.node_t_struct]* %0, [256 x i128]* %1)
  call void @onebyonecpy_hls.p0a4096struct.edge_t_struct.11.12([4096 x %struct.edge_t_struct]* %2, [2048 x i64]* %_0, [2048 x i64]* %_1)
  call fastcc void @onebyonecpy_hls.p0a256i8([256 x i8]* %3, [256 x i8]* align 512 %4)
  call void @onebyonecpy_hls.p0a10i64.13.14([10 x i64]* %5, [5 x i64]* align 512 %_01, [5 x i64]* align 512 %_12)
  ret void
}

; Function Attrs: argmemonly noinline norecurse
define internal fastcc void @onebyonecpy_hls.p0a256struct.node_t_struct.29([256 x %struct.node_t_struct]* noalias, [256 x i128]* noalias readonly) unnamed_addr #2 {
entry:
  %2 = icmp eq [256 x %struct.node_t_struct]* %0, null
  %3 = icmp eq [256 x i128]* %1, null
  %4 = or i1 %2, %3
  br i1 %4, label %ret, label %copy

copy:                                             ; preds = %entry
  br label %for.loop

for.loop:                                         ; preds = %for.loop, %copy
  %for.loop.idx5 = phi i64 [ 0, %copy ], [ %for.loop.idx.next, %for.loop ]
  %5 = getelementptr [256 x i128], [256 x i128]* %1, i64 0, i64 %for.loop.idx5
  %dst.addr.02 = getelementptr [256 x %struct.node_t_struct], [256 x %struct.node_t_struct]* %0, i64 0, i64 %for.loop.idx5, i32 0
  %6 = load i128, i128* %5, align 8
  %.partselect1 = trunc i128 %6 to i64
  store i64 %.partselect1, i64* %dst.addr.02, align 8
  %dst.addr.14 = getelementptr [256 x %struct.node_t_struct], [256 x %struct.node_t_struct]* %0, i64 0, i64 %for.loop.idx5, i32 1
  %7 = lshr i128 %6, 64
  %.partselect = trunc i128 %7 to i64
  store i64 %.partselect, i64* %dst.addr.14, align 8
  %for.loop.idx.next = add nuw nsw i64 %for.loop.idx5, 1
  %exitcond = icmp ne i64 %for.loop.idx.next, 256
  br i1 %exitcond, label %for.loop, label %ret

ret:                                              ; preds = %for.loop, %entry
  ret void
}

declare void @apatb_bfs_hw(i128*, [2048 x i64]*, [2048 x i64]*, i64, i8*, [5 x i64]*, [5 x i64]*)

; Function Attrs: argmemonly noinline norecurse
define internal void @copy_back([256 x %struct.node_t_struct]* noalias "orig.arg.no"="0", [256 x i128]* noalias readonly "orig.arg.no"="1", [4096 x %struct.edge_t_struct]* noalias "orig.arg.no"="2", [2048 x i64]* noalias readonly "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="3" %_0, [2048 x i64]* noalias readonly "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="3" %_1, [256 x i8]* noalias "orig.arg.no"="4", [256 x i8]* noalias readonly align 512 "orig.arg.no"="5", [10 x i64]* noalias "orig.arg.no"="6", [5 x i64]* noalias readonly align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="7" %_01, [5 x i64]* noalias readonly align 512 "fpga.caller.interfaces"="layout_transformed" "orig.arg.no"="7" %_12) #5 {
entry:
  call fastcc void @onebyonecpy_hls.p0a256i8([256 x i8]* %3, [256 x i8]* align 512 %4)
  call void @onebyonecpy_hls.p0a10i64.13.14([10 x i64]* %5, [5 x i64]* align 512 %_01, [5 x i64]* align 512 %_12)
  ret void
}

define void @bfs_hw_stub_wrapper(i128*, [2048 x i64]*, [2048 x i64]*, i64, i8*, [5 x i64]*, [5 x i64]*) #6 {
entry:
  %malloccall = tail call i8* @malloc(i64 4096)
  %7 = bitcast i8* %malloccall to [256 x %struct.node_t_struct]*
  %malloccall1 = tail call i8* @malloc(i64 32768)
  %8 = bitcast i8* %malloccall1 to [4096 x %struct.edge_t_struct]*
  %9 = alloca [10 x i64]
  %10 = bitcast i128* %0 to [256 x i128]*
  %11 = bitcast i8* %4 to [256 x i8]*
  call void @copy_out([256 x %struct.node_t_struct]* %7, [256 x i128]* %10, [4096 x %struct.edge_t_struct]* %8, [2048 x i64]* %1, [2048 x i64]* %2, [256 x i8]* null, [256 x i8]* %11, [10 x i64]* %9, [5 x i64]* %5, [5 x i64]* %6)
  %12 = bitcast [256 x %struct.node_t_struct]* %7 to %struct.node_t_struct*
  %13 = bitcast [4096 x %struct.edge_t_struct]* %8 to %struct.edge_t_struct*
  %14 = bitcast [256 x i8]* %11 to i8*
  %15 = bitcast [10 x i64]* %9 to i64*
  call void @bfs_hw_stub(%struct.node_t_struct* %12, %struct.edge_t_struct* %13, i64 %3, i8* %14, i64* %15)
  call void @copy_in([256 x %struct.node_t_struct]* %7, [256 x i128]* %10, [4096 x %struct.edge_t_struct]* %8, [2048 x i64]* %1, [2048 x i64]* %2, [256 x i8]* null, [256 x i8]* %11, [10 x i64]* %9, [5 x i64]* %5, [5 x i64]* %6)
  ret void
}

declare void @bfs_hw_stub(%struct.node_t_struct*, %struct.edge_t_struct*, i64, i8*, i64*)

attributes #0 = { inaccessiblememonly nounwind }
attributes #1 = { noinline "fpga.wrapper.func"="wrapper" }
attributes #2 = { argmemonly noinline norecurse "fpga.wrapper.func"="onebyonecpy_hls" }
attributes #3 = { nounwind }
attributes #4 = { argmemonly noinline norecurse "fpga.wrapper.func"="copyin" }
attributes #5 = { argmemonly noinline norecurse "fpga.wrapper.func"="copyout" }
attributes #6 = { "fpga.wrapper.func"="stub" }

!llvm.dbg.cu = !{}
!llvm.ident = !{!0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0, !0}
!llvm.module.flags = !{!1, !2, !3}
!blackbox_cfg = !{!4}

!0 = !{!"clang version 7.0.0 "}
!1 = !{i32 2, !"Dwarf Version", i32 4}
!2 = !{i32 2, !"Debug Info Version", i32 3}
!3 = !{i32 1, !"wchar_size", i32 4}
!4 = !{}
!5 = !DILocation(line: 3, column: 9, scope: !6)
!6 = !DILexicalBlockFile(scope: !8, file: !7, discriminator: 0)
!7 = !DIFile(filename: "/mnt/sda1/code/HLSDSE_V2/dataset/MachSuite/random_ds/bfs/bulk/script/dir_0.tcl", directory: "/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk")
!8 = distinct !DISubprogram(name: "bfs", scope: !9, file: !9, line: 9, type: !10, isLocal: false, isDefinition: true, scopeLine: 12, flags: DIFlagPrototyped, isOptimized: false, unit: !38, variables: !4)
!9 = !DIFile(filename: "bfs.c", directory: "/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk")
!10 = !DISubroutineType(types: !11)
!11 = !{null, !12, !25, !30, !31, !37}
!12 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !13, size: 64)
!13 = !DIDerivedType(tag: DW_TAG_typedef, name: "node_t", file: !14, line: 38, baseType: !15)
!14 = !DIFile(filename: "./bfs.h", directory: "/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk")
!15 = distinct !DICompositeType(tag: DW_TAG_structure_type, name: "node_t_struct", file: !14, line: 35, size: 128, elements: !16)
!16 = !{!17, !24}
!17 = !DIDerivedType(tag: DW_TAG_member, name: "edge_begin", scope: !15, file: !14, line: 36, baseType: !18, size: 64)
!18 = !DIDerivedType(tag: DW_TAG_typedef, name: "edge_index_t", file: !14, line: 25, baseType: !19)
!19 = !DIDerivedType(tag: DW_TAG_typedef, name: "uint64_t", file: !20, line: 27, baseType: !21)
!20 = !DIFile(filename: "/usr/include/x86_64-linux-gnu/bits/stdint-uintn.h", directory: "/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk")
!21 = !DIDerivedType(tag: DW_TAG_typedef, name: "__uint64_t", file: !22, line: 45, baseType: !23)
!22 = !DIFile(filename: "/usr/include/x86_64-linux-gnu/bits/types.h", directory: "/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk")
!23 = !DIBasicType(name: "long unsigned int", size: 64, encoding: DW_ATE_unsigned)
!24 = !DIDerivedType(tag: DW_TAG_member, name: "edge_end", scope: !15, file: !14, line: 37, baseType: !18, size: 64, offset: 64)
!25 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !26, size: 64)
!26 = !DIDerivedType(tag: DW_TAG_typedef, name: "edge_t", file: !14, line: 33, baseType: !27)
!27 = distinct !DICompositeType(tag: DW_TAG_structure_type, name: "edge_t_struct", file: !14, line: 28, size: 64, elements: !28)
!28 = !{!29}
!29 = !DIDerivedType(tag: DW_TAG_member, name: "dst", scope: !27, file: !14, line: 32, baseType: !30, size: 64)
!30 = !DIDerivedType(tag: DW_TAG_typedef, name: "node_index_t", file: !14, line: 26, baseType: !19)
!31 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !32, size: 64)
!32 = !DIDerivedType(tag: DW_TAG_typedef, name: "level_t", file: !14, line: 40, baseType: !33)
!33 = !DIDerivedType(tag: DW_TAG_typedef, name: "int8_t", file: !34, line: 24, baseType: !35)
!34 = !DIFile(filename: "/usr/include/x86_64-linux-gnu/bits/stdint-intn.h", directory: "/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk")
!35 = !DIDerivedType(tag: DW_TAG_typedef, name: "__int8_t", file: !22, line: 37, baseType: !36)
!36 = !DIBasicType(name: "signed char", size: 8, encoding: DW_ATE_signed_char)
!37 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !18, size: 64)
!38 = distinct !DICompileUnit(language: DW_LANG_C99, file: !39, producer: "clang version 7.0.0 ", isOptimized: true, runtimeVersion: 0, emissionKind: FullDebug, enums: !4)
!39 = !DIFile(filename: "/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk/bfs_random_prj/solution/.autopilot/db/bfs.pp.0.c", directory: "/mnt/sda1/code/HLSDSE_V2/benchmark/MachSuite/bfs/bulk")
!40 = !DILocation(line: 4, column: 9, scope: !6)
