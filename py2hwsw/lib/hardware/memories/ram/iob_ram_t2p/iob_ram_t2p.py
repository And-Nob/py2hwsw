# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT


def setup(py_params_dict):
    attributes_dict = {
        "version": "0.1",
        "generate_hw": True,
        "confs": [
            {
                "name": "HEXFILE",
                "type": "P",
                "val": '"none"',
                "min": "NA",
                "max": "NA",
                "descr": "Name of file to load into RAM",
            },
            {
                "name": "ADDR_W",
                "type": "P",
                "val": "0",
                "min": "0",
                "max": "NA",
                "descr": "Address bus width",
            },
            {
                "name": "DATA_W",
                "type": "P",
                "val": "0",
                "min": "0",
                "max": "NA",
                "descr": "Data bus width",
            },
            {
                "name": "MEM_INIT_FILE_INT",
                "type": "F",
                "val": "HEXFILE",
                "min": "0",
                "max": "NA",
                "descr": "",
            },
        ],
        "ports": [
            {
                "name": "clk_i",
                "descr": "Clock",
                "signals": [
                    {"name": "clk_i", "width": 1},
                ],
            },
            {
                "name": "w_en_i",
                "descr": "Input port",
                "signals": [
                    {"name": "w_en_i", "width": 1},
                ],
            },
            {
                "name": "w_addr_i",
                "descr": "Input port",
                "signals": [
                    {"name": "w_addr_i", "width": "ADDR_W"},
                ],
            },
            {
                "name": "w_data_i",
                "descr": "Input port",
                "signals": [
                    {"name": "w_data_i", "width": "DATA_W"},
                ],
            },
            {
                "name": "r_en_i",
                "descr": "Input port",
                "signals": [
                    {"name": "r_en_i", "width": 1},
                ],
            },
            {
                "name": "r_addr_i",
                "descr": "Input port",
                "signals": [
                    {"name": "r_addr_i", "width": "ADDR_W"},
                ],
            },
            {
                "name": "r_data_o",
                "descr": "Output port",
                "signals": [
                    {"name": "r_data_o", "width": "DATA_W"},
                ],
            },
        ],
        "snippets": [
            {
                "verilog_code": """



   localparam INIT_RAM = (MEM_INIT_FILE_INT != "none") ? 1 : 0;
   // Declare the RAM
   reg [DATA_W-1:0] mem    [(2**ADDR_W)-1:0];

   reg [DATA_W-1:0] r_data;
   // Initialize the RAM
   generate
       if (INIT_RAM) begin : mem_init
           initial $readmemh(MEM_INIT_FILE_INT, mem, 0, (2 ** ADDR_W) - 1);
       end
   endgenerate

   //read port
   always @(posedge clk_i) begin
       if (r_en_i) begin
           r_data <= mem[r_addr_i];
       end
   end

   //write port
   always @(posedge clk_i) begin
       if (w_en_i) begin
           mem[w_addr_i] <= w_data_i;
       end
   end

   assign r_data_o = r_data;
            """,
            },
        ],
    }

    return attributes_dict
