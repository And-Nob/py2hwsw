`timescale 1ns / 1ps
`include "iob_utils.vh"
`include "iob_axistream_out_conf.vh"
`include "iob_axistream_out_swreg_def.vh"

module iob_axistream_out #(
`include "iob_axistream_out_params.vs"
                           ) (
`include "iob_axistream_out_io.vs"
                              );

   //
   // Connection wires
   //
`include "iob_wire.vs"

   //rst and enble synced to axis_clk
   wire                 axis_sw_rst;
   wire                 axis_sw_enable;
   
   //fifo write
   wire                   fifo_write;
   wire [DATA_W-1:0]      fifo_wdata;
   wire [DATA_W-1:0]      cpu_data, dma_data;

   //fifo read
   reg                    axis_fifo_empty;
   reg                    axis_fifo_read;
   wire                   axis_fifo_read_q;
   reg                    pcounter, pcounter_nxt;

   //word counter
   wire [DATA_W-1:0]      axis_word_count;
   wire [DATA_W-1:0]      axis_nwords;
   
   //
   wire [TDATA_W-1:0]     axis_data;
   wire                   axis_tvalid;
     
   //fifo RAM
   wire                   ext_mem_w_clk;
   wire                   ext_mem_w_en;
   wire [FIFO_ADDR_W-1:0] ext_mem_w_addr;
   wire [DATA_W-1:0]      ext_mem_w_data;
   wire                   ext_mem_r_clk;
   wire                   ext_mem_r_en;
   wire [FIFO_ADDR_W-1:0] ext_mem_r_addr;
   wire [DATA_W-1:0]      ext_mem_r_data;
   
   // configuration control and status register file.
`include "iob_axistream_out_swreg_inst.vs"
   
   //connect iob signals to ports
   assign iob_valid = iob_valid_i;
   assign iob_addr = iob_addr_i;
   assign iob_wdata = iob_wdata_i;
   assign iob_wstrb = iob_wstrb_i;
   assign iob_rvalid_o = iob_rvalid;
   assign iob_rdata_o = iob_rdata;
   assign iob_ready_o = iob_ready;


   //CPU data ready and interrupt
   assign DATA_wready_wr = ~FIFO_FULL_rd;
   assign interrupt_o = FIFO_LEVEL_rd <= FIFO_THRESHOLD_wr;
   
   //DMA data ready
   assign dma_tready_o =  ~FIFO_FULL_rd;
   

   //FIFO write
   assign fifo_write = (DATA_wen_wr | dma_tvalid_i) & ~FIFO_FULL_rd;
   assign fifo_wdata = dma_tvalid_i==1'b1 ? dma_tdata_i : DATA_wdata_wr;

   //FIFO read
   always @* begin
      pcounter_nxt = pcounter+1'b1;
      axis_fifo_read = 1'b0;
      
      if (pcounter == 0) begin
         if (axis_fifo_empty) begin
            pcounter_nxt = pcounter;
         end else begin
            axis_fifo_read = 1'b1;
         end
      end else begin
         if (!axis_tready_i) begin
            pcounter_nxt = pcounter;
         end else if (axis_fifo_empty) begin
               pcounter_nxt = 0;
         end else begin
            axis_fifo_read = 1'b1;
         end
      end
   end


   //AXI stream
   assign axis_tdata_o = axis_data[TDATA_W-1:0];
   assign axis_tvalid_o = axis_fifo_read_q;
   assign axis_tlast_o = (axis_word_count == axis_nwords) & axis_tvalid_o;


   //
   // Submodules
   //

   // fifo read register
   iob_reg_re #(
                .DATA_W (1),
                .RST_VAL(1'd0)
                ) fifo_read_reg (
                              .clk_i (axis_clk_i),
                              .cke_i (axis_cke_i),
                              .arst_i(axis_arst_i),
                              .rst_i (axis_sw_rst),
                              .en_i  (axis_sw_enable),
                              .data_i(axis_fifo_read),
                              .data_o(axis_fifo_read_q)
                              );

   // program counter
   iob_reg_re #(
                .DATA_W (1),
                .RST_VAL(1'd0)
                ) tvalid_reg (
                              .clk_i (axis_clk_i),
                              .cke_i (axis_cke_i),
                              .arst_i(axis_arst_i),
                              .rst_i (axis_sw_rst),
                              .en_i  (axis_sw_enable),
                              .data_i(pcounter_nxt),
                              .data_o(pcounter)
                              );


   // sent words counter
   iob_counter #(
                 .DATA_W (DATA_W),
                 .RST_VAL(0)
                 ) word_count_inst (
                                    .clk_i (axis_clk_i),
                                    .cke_i (axis_sw_enable),
                                    .arst_i(axis_arst_i),
                                    .rst_i (axis_sw_rst),
                                    .en_i  (axis_fifo_read),
                                    .data_o(axis_word_count)
                                    );

   
   //Synchronizers from sw_regs to axis domain
   iob_sync #(
              .DATA_W (1),
              .RST_VAL(1'd0)
              ) sw_rst (
                        .clk_i   (axis_clk_i),
                        .arst_i  (axis_arst_i),
                        .signal_i(SOFT_RESET_wr),
                        .signal_o(axis_sw_rst)
                        );

   iob_sync #(
              .DATA_W (1),
              .RST_VAL(1'd0)
              ) sw_enable (
                           .clk_i   (axis_clk_i),
                           .arst_i  (axis_arst_i),
                           .signal_i(ENABLE_wr),
                           .signal_o(axis_sw_enable)
                           );

   iob_sync #(
              .DATA_W (DATA_W),
              .RST_VAL(0)
              ) fifo_threshold (
                                .clk_i   (axis_clk_i),
                                .arst_i  (axis_arst_i),
                                .signal_i(NWORDS_wr),
                                .signal_o(axis_nwords)
                                );


   // fifo memories
   iob_ram_t2p #(
                 .DATA_W(TDATA_W),
                 .ADDR_W(FIFO_ADDR_W)
                 ) iob_ram_t2p (
                                .w_clk_i (ext_mem_w_clk),
                                .w_en_i  (ext_mem_w_en),
                                .w_addr_i(ext_mem_w_addr),
                                .w_data_i(ext_mem_w_data),
                                
                                .r_clk_i (ext_mem_r_clk),
                                .r_en_i  (ext_mem_r_en),
                                .r_addr_i(ext_mem_r_addr),
                                .r_data_o(ext_mem_r_data)
                                );

   //async fifo
   iob_fifo_async #(
                    .W_DATA_W(DATA_W),
                    .R_DATA_W(TDATA_W),
                    .ADDR_W  (FIFO_ADDR_W)
                    ) data_fifo (
                                 //memory write port
                                 .ext_mem_w_clk_o (ext_mem_w_clk),
                                 .ext_mem_w_en_o  (ext_mem_w_en),
                                 .ext_mem_w_addr_o(ext_mem_w_addr),
                                 .ext_mem_w_data_o(ext_mem_w_data),
                                 //memory read port
                                 .ext_mem_r_clk_o (ext_mem_r_clk),
                                 .ext_mem_r_en_o  (ext_mem_r_en),
                                 .ext_mem_r_addr_o(ext_mem_r_addr),
                                 .ext_mem_r_data_i(ext_mem_r_data),
                                 //read port (axis clk domain)
                                 .r_clk_i         (axis_clk_i),
                                 .r_cke_i         (axis_cke_i),
                                 .r_arst_i        (axis_arst_i),
                                 .r_rst_i         (axis_sw_rst),
                                 .r_en_i          (axis_fifo_read),
                                 .r_data_o        (axis_data),
                                 .r_empty_o       (axis_fifo_empty),
                                 .r_full_o        (),
                                 .r_level_o       (),
                                 //write port (sys clk domain)
                                 .w_clk_i         (clk_i),
                                 .w_cke_i         (cke_i),
                                 .w_arst_i        (arst_i),
                                 .w_rst_i         (SOFT_RESET_wr),
                                 .w_en_i          (fifo_write),
                                 .w_data_i        (fifo_wdata),
                                 .w_empty_o       (EMPTY_rd),
                                 .w_full_o        (FULL_rd),
                                 .w_level_o       (FIFO_LEVEL_rd)
                                 );
   
endmodule


