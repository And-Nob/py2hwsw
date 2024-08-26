#!/usr/bin/env python3
#
#    csr_gen.py: build Verilog software accessible registers and software getters and setters
#

import sys
import os
from math import ceil, log, log2
from latex import write_table
import iob_colors
import re


def clog2(val):
    """Used by eval_param_expression"""
    return ceil(log2(val))


def eval_param_expression(param_expression, params_dict):
    """Given a mathematical string with parameters, replace every parameter by
    its numeric value and tries to evaluate the string.
    param_expression: string defining a math expression that may contain parameters
    params_dict: dictionary of parameters, where the key is the parameter name and the value is its value
    """
    if type(param_expression) is int:
        return param_expression
    else:
        original_expression = param_expression
        # Split string to separate parameters/macros from the rest
        split_expression = re.split(r"([^\w_])", param_expression)
        # Replace each parameter, following the reverse order of parameter list.
        # The reversed order allows replacing parameters recursively (parameters may
        # have values with parameters that came before).
        for param_name, param_value in reversed(params_dict.items()):
            # Replace every instance of this parameter by its value
            for idx, word in enumerate(split_expression):
                if word == param_name:
                    # Replace parameter/macro by its value
                    split_expression[idx] = param_value
                    # Remove '`' char if it was a macro
                    if idx > 0 and split_expression[idx - 1] == "`":
                        split_expression[idx - 1] = ""
                    # resplit the string in case the parameter value contains other parameters
                    split_expression = re.split(r"([^\w_])", "".join(split_expression))
        # Join back the string
        param_expression = "".join(split_expression)
        # Evaluate $clog2 expressions
        param_expression = param_expression.replace("$clog2", "clog2")
        # Evaluate IOB_MAX and IOB_MIN expressions
        param_expression = param_expression.replace("`IOB_MAX", "max")
        param_expression = param_expression.replace("`IOB_MIN", "min")

        # Try to calculate string as it should only contain numeric values
        try:
            return eval(param_expression)
        except:
            sys.exit(
                f"Error: string '{original_expression}' evaluated to '{param_expression}' is not a numeric expression."
            )


def eval_param_expression_from_config(param_expression, confs, param_attribute):
    """Given a mathematical string with parameters, replace every parameter by its
    numeric value and tries to evaluate the string. The parameters are taken from the
    confs dictionary.
    param_expression: string defining a math expression that may contain parameters.
    confs: list of dictionaries, each of which describes a parameter and has attributes:
           'name', 'val' and 'max'.
    param_attribute: name of the attribute in the paramater that contains the value to
           replace in string given. Attribute names are: 'val', 'min, or 'max'.
    """
    # Create parameter dictionary with correct values to be replaced in string
    params_dict = {}
    for param in confs:
        params_dict[param["name"]] = param[param_attribute]

    return eval_param_expression(param_expression, params_dict)


class csr_gen:
    """Use a class for the entire module, as it may be imported multiple times, but
    must have instance variables (multiple cores/submodules have different registers)
    """

    def __init__(self):
        self.cpu_n_bytes = 4
        self.core_addr_w = None
        self.config = None

    @staticmethod
    def boffset(n, n_bytes):
        return 8 * (n % n_bytes)

    @staticmethod
    def bfloor(n, log2base):
        base = int(2**log2base)
        if n % base == 0:
            return n
        return base * int(n / base)

    @staticmethod
    def verilog_max(a, b):
        if a == b:
            return a
        try:
            # Assume a and b are int
            a = int(a)
            b = int(b)
            return a if a > b else b
        except ValueError:
            # a or b is a string
            return f"(({a} > {b}) ? {a} : {b})"

    def get_reg_table(self, regs, rw_overlap, autoaddr):
        # Create reg table
        reg_table = []
        for i_regs in regs:
            reg_table += i_regs.regs

        return self.compute_addr(reg_table, rw_overlap, autoaddr)

    def bceil(self, n, log2base):
        base = int(2**log2base)
        n = eval_param_expression_from_config(n, self.config, "max")
        # print(f"{n} of {type(n)} and {base}")
        if n % base == 0:
            return n
        else:
            return int(base * ceil(n / base))

    # Calculate numeric value of addr_w, replacing params by their max value
    def calc_addr_w(self, log2n_items, n_bytes):
        return int(
            ceil(
                eval_param_expression_from_config(log2n_items, self.config, "max")
                + log(n_bytes, 2)
            )
        )

    # Generate symbolic expression string to caluclate addr_w in verilog
    @staticmethod
    def calc_verilog_addr_w(log2n_items, n_bytes):
        n_bytes = int(n_bytes)
        try:
            # Assume log2n_items is int
            log2n_items = int(log2n_items)
            return log2n_items + ceil(log(n_bytes, 2))
        except ValueError:
            # log2n_items is a string
            if n_bytes == 1:
                return log2n_items
            else:
                return f"{log2n_items}+{ceil(log(n_bytes, 2))}"

    def gen_wr_reg(self, row):
        name = row.name
        rst_val = int(row.rst_val)
        n_bits = row.n_bits
        log2n_items = row.log2n_items
        n_bytes = self.bceil(n_bits, 3) / 8
        if n_bytes == 3:
            n_bytes = 4
        addr = row.addr
        addr_w = self.calc_verilog_addr_w(log2n_items, n_bytes)
        auto = row.autoreg

        lines = ""
        lines += f"\n\n//NAME: {name};\n//TYPE: {row.type}; WIDTH: {n_bits}; RST_VAL: {rst_val}; ADDR: {addr}; SPACE (bytes): {2**self.calc_addr_w(log2n_items, n_bytes)} (max); AUTO: {auto}\n\n"

        # compute wdata with only the needed bits
        lines += f"    wire [{self.verilog_max(n_bits, 1)}-1:0] {name}_wdata; \n"
        lines += f"    assign {name}_wdata = iob_wdata_i[{self.boffset(addr,self.cpu_n_bytes)}+:{self.verilog_max(n_bits,1)}];\n"

        # signal to indicate if the register is addressed
        lines += f"    wire {name}_addressed_w;\n"

        # test if addr and addr_w are int and substitute with their values
        if isinstance(addr, int) and isinstance(addr_w, int):
            lines += f"    assign {name}_addressed_w = (waddr >= {addr}) && (waddr < {addr+2**addr_w});\n"
        else:
            lines += f"    assign {name}_addressed_w = (waddr >= {addr}) && (waddr < ({addr}+(2**({addr_w}))));\n"

        if auto:  # generate register
            # fill remaining bits with 0s
            if isinstance(n_bits, str):
                if rst_val != 0:
                    # get number of bits needed to represent rst_val
                    rst_n_bits = ceil(log(rst_val + 1, 2))
                    zeros_filling = (
                        "{(" + str(n_bits) + "-" + str(rst_n_bits) + "){1'd0}}"
                    )
                    rst_val_str = (
                        "{"
                        + zeros_filling
                        + ","
                        + str(rst_n_bits)
                        + "'d"
                        + str(rst_val)
                        + "}"
                    )
                else:
                    rst_val_str = "{" + str(n_bits) + "{1'd0}}"
            else:
                rst_val_str = str(n_bits) + "'d" + str(rst_val)
            lines += f"    wire {name}_wen;\n"
            lines += f"    assign {name}_wen = (iob_valid_i & iob_ready_o) & ((|iob_wstrb_i) & {name}_addressed_w);\n"
            lines += "    iob_reg_e #(\n"
            lines += f"      .DATA_W({n_bits}),\n"
            lines += f"      .RST_VAL({rst_val_str})\n"
            lines += f"    ) {name}_datareg (\n"
            lines += "      .clk_i  (clk_i),\n"
            lines += "      .cke_i  (cke_i),\n"
            lines += "      .arst_i (arst_i),\n"
            lines += f"      .en_i   ({name}_wen),\n"
            lines += f"      .data_i ({name}_wdata),\n"
            lines += f"      .data_o ({name}_o)\n"
            lines += "    );\n"
        else:  # compute wen
            lines += f"    assign {name}_wen_o = ({name}_addressed_w & (iob_valid_i & iob_ready_o))? |iob_wstrb_i: 1'b0;\n"
            lines += f"    assign {name}_wdata_o = {name}_wdata;\n"

        return lines

    def gen_rd_reg(self, row):
        name = row.name
        rst_val = row.rst_val
        n_bits = row.n_bits
        log2n_items = row.log2n_items
        n_bytes = self.bceil(n_bits, 3) / 8
        if n_bytes == 3:
            n_bytes = 4
        addr = row.addr
        addr_w = self.calc_verilog_addr_w(log2n_items, n_bytes)
        auto = row.autoreg

        lines = ""
        lines += f"\n\n//NAME: {name};\n//TYPE: {row.type}; WIDTH: {n_bits}; RST_VAL: {rst_val}; ADDR: {addr}; SPACE (bytes): {2**self.calc_addr_w(log2n_items,n_bytes)} (max); AUTO: {auto}\n\n"

        if not auto:  # output read enable
            lines += f"    wire {name}_addressed_r;\n"
            lines += f"    assign {name}_addressed_r = (iob_addr_i >= {addr}) && (iob_addr_i < ({addr}+(2**({addr_w}))));\n"
            lines += f"    assign {name}_ren_o = {name}_addressed_r & (iob_valid_i & iob_ready_o) & (~|iob_wstrb_i);\n"

        return lines

    # generate ports for csrs module
    def gen_port(self, table, f):
        for row in table:
            name = row.name
            n_bits = row.n_bits
            auto = row.autoreg

            # version is not a register, it is an internal constant
            if name != "version":
                if "W" in row.type:
                    if auto:
                        f.write(
                            f"    output [{self.verilog_max(n_bits,1)}-1:0] {name}_o,\n"
                        )
                    else:
                        f.write(
                            f"    output [{self.verilog_max(n_bits,1)}-1:0] {name}_wdata_o,\n"
                        )
                        f.write(f"    output {name}_wen_o,\n")
                        f.write(f"    input {name}_wready_i,\n")
                if "R" in row.type:
                    if auto:
                        f.write(
                            f"    input [{self.verilog_max(n_bits,1)}-1:0] {name}_i,\n"
                        )
                    else:
                        f.write(
                            f"""
    input [{self.verilog_max(n_bits, 1)}-1:0] {name}_rdata_i,
    input {name}_rvalid_i,
    output {name}_ren_o,
    input {name}_rready_i,
"""
                        )

    # auxiliar read register case name
    def aux_read_reg_case_name(self, row):
        aux_read_reg_case_name = ""
        if "R" in row.type:
            addr = row.addr
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            addr_w_base = max(log(self.cpu_n_bytes, 2), addr_w)
            aux_read_reg_case_name = f"iob_addr_i_{self.bfloor(addr, addr_w_base)}_{self.boffset(addr, self.cpu_n_bytes)}"
        return aux_read_reg_case_name

    # generate wires to connect instance in top module
    def gen_inst_wire(self, table, f):
        for row in table:
            name = row.name
            n_bits = row.n_bits
            auto = row.autoreg

            # version is not a register, it is an internal constant
            if name != "version":
                if "W" in row.type:
                    if auto:
                        f.write(
                            f"    wire [{self.verilog_max(n_bits,1)}-1:0] {name}_wr;\n"
                        )
                    else:
                        f.write(
                            f"    wire [{self.verilog_max(n_bits,1)}-1:0] {name}_wdata_wr;\n"
                        )
                        f.write(f"    wire {name}_wen_wr;\n")
                        f.write(f"    wire {name}_wready_wr;\n")
                if "R" in row.type:
                    if auto:
                        f.write(
                            f"    wire [{self.verilog_max(n_bits,1)}-1:0] {name}_rd;\n"
                        )
                    else:
                        f.write(
                            f"""
    wire [{self.verilog_max(n_bits,1)}-1:0] {name}_rdata_rd;
    wire {name}_rvalid_rd;
    wire {name}_ren_rd;
    wire {name}_rready_rd;
"""
                        )
        f.write("\n")

    # generate portmap for csrs instance in top module
    def gen_portmap(self, table, f):
        for row in table:
            name = row.name
            auto = row.autoreg

            # version is not a register, it is an internal constant
            if name != "version":
                if "W" in row.type:
                    if auto:
                        f.write(f"    .{name}_o({name}_wr),\n")
                    else:
                        f.write(f"    .{name}_wdata_o({name}_wdata_wr),\n")
                        f.write(f"    .{name}_wen_o({name}_wen_wr),\n")
                        f.write(f"    .{name}_wready_i({name}_wready_wr),\n")
                if "R" in row.type:
                    if auto:
                        f.write(f"    .{name}_i({name}_rd),\n")
                    else:
                        f.write(
                            f"""
    .{name}_rdata_i({name}_rdata_rd),
    .{name}_rvalid_i({name}_rvalid_rd),
    .{name}_ren_o({name}_ren_rd),
    .{name}_rready_i({name}_rready_rd),
"""
                        )

    def gen_ports(self, table):
        """Generate ports for csrs instance"""
        ports = []
        for row in table:
            name = row.name
            auto = row.autoreg
            n_bits = row.n_bits
            register_signals = []

            # version is not a register, it is an internal constant
            if name == "version":
                continue

            if "W" in row.type:
                if auto:
                    register_signals.append({
                        "name": name,
                        "direction": "output",
                        "width": self.verilog_max(n_bits, 1),
                    })
                else:
                    register_signals += [
                        {
                            "name": f"{name}_wdata",
                            "direction": "output",
                            "width": self.verilog_max(n_bits, 1),
                        },
                        {
                            "name": f"{name}_wen",
                            "direction": "output",
                            "width": "1",
                        },
                        {
                            "name": f"{name}_wready",
                            "direction": "input",
                            "width": "1",
                        },
                    ]
            if "R" in row.type:
                if auto:
                    register_signals.append({
                        "name": name,
                        "direction": "input",
                        "width": self.verilog_max(n_bits, 1),
                    })
                else:
                    register_signals += [
                        {
                            "name": f"{name}_rdata",
                            "direction": "input",
                            "width": self.verilog_max(n_bits, 1),
                        },
                        {
                            "name": f"{name}_rvalid",
                            "direction": "input",
                            "width": "1",
                        },
                        {
                            "name": f"{name}_ren",
                            "direction": "output",
                            "width": "1",
                        },
                        {
                            "name": f"{name}_rready",
                            "direction": "input",
                            "width": "1",
                        },
                    ]

            ports.append({
                "name": name,
                "descr": f"{name} register interface",
                "signals": register_signals,
            })

        return ports

    def get_csrs_inst_params(self, core_confs):
        """Return multi-line string with parameters for csrs instance"""
        param_list = [p for p in core_confs if p["type"] == "P"]
        if not param_list:
            return ""

        param_str = "#(\n"
        for idx, param in enumerate(param_list):
            comma = "," if idx < len(param_list) - 1 else ""
            param_str += f"    .{param['name']}({param['name']}){comma}\n"
        param_str += ") "
        return param_str

    def write_hwcode(self, table, core_attributes):
        """ Generates and appends verilog code to core "snippets" list.
        """

        wires = []
        snippet = ""
        # macros
        snippet += """
    `define IOB_NBYTES (DATA_W/8)
    `define IOB_NBYTES_W $clog2(`IOB_NBYTES)
    `define IOB_WORD_ADDR(ADDR) ((ADDR>>`IOB_NBYTES_W)<<`IOB_NBYTES_W)\n
"""

        snippet += """
    localparam WSTRB_W = DATA_W/8;

    //FSM states
    localparam WAIT_REQ = 1'd0;
    localparam WAIT_RVALID = 1'd1;
"""
        wires.append(
            {
                "name": "state",
                "descr": "",
                "signals": [
                    {"name": "state", "width": 1},
                ],
            },
        )


        # write address
        snippet += "\n    //write address\n"

        # extract address byte offset
        snippet += "    wire [($clog2(WSTRB_W)+1)-1:0] byte_offset;\n"
        snippet += "    iob_ctls #(.W(WSTRB_W), .MODE(0), .SYMBOL(0)) bo_inst (.data_i(iob_wstrb_i), .count_o(byte_offset));\n"

        # compute write address
        snippet += "    wire [ADDR_W-1:0] waddr;\n"
        snippet += "    assign waddr = `IOB_WORD_ADDR(iob_addr_i) + byte_offset;\n"

        # insert write register logic
        for row in table:
            if "W" in row.type:
                snippet += self.gen_wr_reg(row)

        # insert read register logic
        for row in table:
            if "R" in row.type:
                snippet += self.gen_rd_reg(row)

        #
        # RESPONSE SWITCH
        #
        snippet += "\n\n//RESPONSE SWITCH\n\n"

        # use variables to compute response
        snippet += """
    assign iob_rvalid_o = rvalid;
    assign iob_rdata_o = rdata;
    assign iob_ready_o = ready;

"""
        wires += [
            # Implicit "iob_reg"
            {
                "name": "rvalid",
                "descr": "",
                "signals": [
                    {"name": "rvalid", "width": 1},
                ],
            },
            {
                "name": "rdata",
                "descr": "",
                "signals": [
                    {"name": "rdata", "width": 8*self.cpu_n_bytes},
                ],
            },
            {
                "name": "ready",
                "descr": "",
                "signals": [
                    {"name": "ready", "width": 1},
                ],
            },
            # Wires of type "reg"
            {
                "name": "rvalid_int",
                "descr": "",
                "signals": [
                    {"name": "rvalid_int", "width": 1},
                ],
            },
            {
                "name": "wready_int",
                "descr": "",
                "signals": [
                    {"name": "wready_int", "width": 1},
                ],
            },
            {
                "name": "rready_int",
                "descr": "",
                "signals": [
                    {"name": "rready_int", "width": 1},
                ],
            },
        ]

        # auxiliar read register cases
        for row in table:
            if "R" in row.type:
                aux_read_reg = self.aux_read_reg_case_name(row)
                if aux_read_reg:
                    wires.append(
                        {
                            "name": aux_read_reg,
                            "descr": "",
                            "signals": [
                                {"name": aux_read_reg, "width": 1},
                            ],
                        },
                    )

        snippet += f"""
    always @* begin
        rdata_nxt = {8*self.cpu_n_bytes}'d0;
        rvalid_int = (iob_valid_i & iob_ready_o) & (~(|iob_wstrb_i));
        rready_int = 1'b1;
        wready_int = 1'b1;

"""

        # read register response
        for row in table:
            name = row.name
            addr = row.addr
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            addr_last = int(
                addr
                + (
                    (
                        2
                        ** eval_param_expression_from_config(
                            log2n_items, self.config, "max"
                        )
                    )
                )
                * n_bytes
            )
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            addr_w_base = max(log(self.cpu_n_bytes, 2), addr_w)
            auto = row.autoreg

            if "R" in row.type:
                aux_read_reg = self.aux_read_reg_case_name(row)

                if self.bfloor(addr, addr_w_base) == self.bfloor(
                    addr_last, addr_w_base
                ):
                    snippet += f"        {aux_read_reg} = (`IOB_WORD_ADDR(iob_addr_i) == {self.bfloor(addr, addr_w_base)});\n"
                    snippet += f"        if({aux_read_reg}) "
                else:
                    snippet += f"            {aux_read_reg} = ((`IOB_WORD_ADDR(iob_addr_i) >= {self.bfloor(addr, addr_w_base)}) && (`IOB_WORD_ADDR(iob_addr_i) < {self.bfloor(addr_last, addr_w_base)}));\n"
                    snippet += f"        if({aux_read_reg}) "
                snippet += f"begin\n"
                if name == "version":
                    rst_val = row.rst_val
                    snippet += f"            rdata_nxt[{self.boffset(addr, self.cpu_n_bytes)}+:{8*n_bytes}] = 16'h{rst_val}|{8*n_bytes}'d0;\n"
                elif auto:
                    snippet += f"            rdata_nxt[{self.boffset(addr, self.cpu_n_bytes)}+:{8*n_bytes}] = {name}_i|{8*n_bytes}'d0;\n"
                else:
                    snippet += f"""
            rdata_nxt[{self.boffset(addr, self.cpu_n_bytes)}+:{8*n_bytes}] = {name}_rdata_i|{8*n_bytes}'d0;
            rvalid_int = {name}_rvalid_i;
"""
                if not auto:
                    snippet += f"            rready_int = {name}_rready_i;\n"
                snippet += "        end\n\n"

        # write register response
        for row in table:
            name = row.name
            addr = row.addr
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            auto = row.autoreg

            if "W" in row.type:
                if not auto:
                    # get wready
                    snippet += f"        if((waddr >= {addr}) && (waddr < {addr + 2**addr_w})) begin\n"
                    snippet += f"            wready_int = {name}_wready_i;\n        end\n"

        snippet += """

        // ######  FSM  #############

        //FSM default values
        ready_nxt = 1'b0;
        rvalid_nxt = 1'b0;
        state_nxt = state;

        //FSM state machine
        case(state)
            WAIT_REQ: begin
                if(iob_valid_i & (!iob_ready_o)) begin // Wait for a valid request
                    ready_nxt = |iob_wstrb_i ? wready_int : rready_int;
                    // If is read and ready, go to WAIT_RVALID
                    if (ready_nxt && (!(|iob_wstrb_i))) begin
                        state_nxt = WAIT_RVALID;
                    end
                end
            end

            default: begin  // WAIT_RVALID
                if(rvalid_int) begin
                    rvalid_nxt = 1'b1;
                    state_nxt = WAIT_REQ;
                end
            end
        endcase

    end //always @*
"""

        core_attributes["wires"] += wires
        core_attributes["snippets"] += [
            {"verilog_code": snippet}
        ]

    def write_lparam_header(self, table, out_dir, top):
        """ Generate *_csrs_lparam.vs file. Macros from this file contain the default
        values of the registers. These should not be used inside the instance of
        the core/system.
        """
        os.makedirs(out_dir, exist_ok=True)
        f_def = open(f"{out_dir}/{top}_csrs_lparam.vs", "w")
        f_def.write("//used address space width\n")
        addr_w_prefix = f"{top}_csrs".upper()
        f_def.write(f"localparam {addr_w_prefix}_ADDR_W = {self.core_addr_w};\n\n")
        f_def.write("//These macros only contain default values for the registers\n")
        f_def.write("//address macros\n")
        macro_prefix = f"{top}_".upper()
        f_def.write("//addresses\n")
        for row in table:
            name = row.name.upper()
            n_bits = row.n_bits
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            log2n_items = row.log2n_items
            addr_w = int(
                ceil(
                    eval_param_expression_from_config(log2n_items, self.config, "val")
                    + log(n_bytes, 2)
                )
            )
            f_def.write(f"localparam {macro_prefix}{name}_ADDR = {row.addr};\n")
            if eval_param_expression_from_config(log2n_items, self.config, "val") > 0:
                f_def.write(f"localparam {macro_prefix}{name}_ADDR_W = {addr_w};\n")
            f_def.write(
                f"localparam {macro_prefix}{name}_W = {eval_param_expression_from_config(n_bits, self.config,'val')};\n\n"
            )
        f_def.close()

    def write_hwheader(self, table, out_dir, top):
        """ Generate *_csrs_def.vh file. Macros from this file should only be used
        inside the instance of the core/system since they may contain parameters which
        are only known by the instance.
        """
        os.makedirs(out_dir, exist_ok=True)
        f_def = open(f"{out_dir}/{top}_csrs_def.vh", "w")
        f_def.write(f'`include "{top}_csrs_conf.vh"\n')
        f_def.write("//These macros may be dependent on instance parameters\n")
        f_def.write("//address macros\n")
        macro_prefix = f"{top}_".upper()
        f_def.write("//addresses\n")
        for row in table:
            name = row.name.upper()
            n_bits = row.n_bits
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            log2n_items = row.log2n_items
            f_def.write(f"`define {macro_prefix}{name}_ADDR {row.addr}\n")
            if eval_param_expression_from_config(log2n_items, self.config, "max") > 0:
                f_def.write(
                    f"`define {macro_prefix}{name}_ADDR_W {self.verilog_max(self.calc_verilog_addr_w(log2n_items,n_bytes),1)}\n"
                )
            f_def.write(
                f"`define {macro_prefix}{name}_W {self.verilog_max(n_bits,1)}\n\n"
            )
        f_def.close()

    # Get C type from csrs n_bytes
    # uses unsigned int types from C stdint library
    @staticmethod
    def csr_type(name, n_bytes):
        type_dict = {1: "uint8_t", 2: "uint16_t", 4: "uint32_t", 8: "uint64_t"}
        try:
            type_try = type_dict[n_bytes]
        except:
            print(
                f"{iob_colors.FAIL}register {name} has invalid number of bytes {n_bytes}.{iob_colors.ENDC}"
            )
            type_try = -1
        return type_try

    def write_swheader(self, table, out_dir, top):
        os.makedirs(out_dir, exist_ok=True)
        fswhdr = open(f"{out_dir}/{top}_csrs.h", "w")

        core_prefix = f"{top}_".upper()

        fswhdr.write(f"#ifndef H_{core_prefix}CSRS_H\n")
        fswhdr.write(f"#define H_{core_prefix}CSRS_H\n\n")
        fswhdr.write("#include <stdint.h>\n\n")

        fswhdr.write("//used address space width\n")
        fswhdr.write(f"#define  {core_prefix}CSRS_ADDR_W {self.core_addr_w}\n\n")

        fswhdr.write("//Addresses\n")
        for row in table:
            name = row.name.upper()
            if "W" in row.type or "R" in row.type:
                fswhdr.write(f"#define {core_prefix}{name}_ADDR {row.addr}\n")

        fswhdr.write("\n//Data widths (bit)\n")
        for row in table:
            name = row.name.upper()
            n_bits = row.n_bits
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            if "W" in row.type or "R" in row.type:
                fswhdr.write(f"#define {core_prefix}{name}_W {n_bytes*8}\n")

        fswhdr.write("\n// Base Address\n")
        fswhdr.write(f"void {core_prefix}INIT_BASEADDR(uint32_t addr);\n")

        fswhdr.write("\n// Core Setters and Getters\n")
        for row in table:
            name = row.name
            name_upper = name.upper()
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if "W" in row.type:
                sw_type = self.csr_type(name, n_bytes)
                addr_arg = ""
                if addr_w / n_bytes > 1:
                    addr_arg = ", int addr"
                fswhdr.write(
                    f"void {core_prefix}SET_{name_upper}({sw_type} value{addr_arg});\n"
                )
            if "R" in row.type:
                sw_type = self.csr_type(name, n_bytes)
                addr_arg = ""
                if addr_w / n_bytes > 1:
                    addr_arg = "int addr"
                fswhdr.write(f"{sw_type} {core_prefix}GET_{name_upper}({addr_arg});\n")

        fswhdr.write(f"\n#endif // H_{core_prefix}_CSRS_H\n")

        fswhdr.close()

    def write_swcode(self, table, out_dir, top):
        os.makedirs(out_dir, exist_ok=True)
        fsw = open(f"{out_dir}/{top}_csrs_emb.c", "w")
        core_prefix = f"{top}_".upper()
        fsw.write(f'#include "{top}_csrs.h"\n\n')
        fsw.write("\n// Base Address\n")
        fsw.write("static int base;\n")
        fsw.write(f"void {core_prefix}INIT_BASEADDR(uint32_t addr) {{\n")
        fsw.write("  base = addr;\n")
        fsw.write("}\n")

        fsw.write("\n// Core Setters and Getters\n")

        for row in table:
            name = row.name
            name_upper = name.upper()
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if "W" in row.type:
                sw_type = self.csr_type(name, n_bytes)
                addr_arg = ""
                addr_arg = ""
                addr_shift = ""
                if addr_w / n_bytes > 1:
                    addr_arg = ", int addr"
                    addr_shift = f" + (addr << {int(log(n_bytes, 2))})"
                fsw.write(
                    f"void {core_prefix}SET_{name_upper}({sw_type} value{addr_arg}) {{\n"
                )
                fsw.write(
                    f"  (*( (volatile {sw_type} *) ( (base) + ({core_prefix}{name_upper}_ADDR){addr_shift}) ) = (value));\n"
                )
                fsw.write("}\n\n")
            if "R" in row.type:
                sw_type = self.csr_type(name, n_bytes)
                addr_arg = ""
                addr_shift = ""
                if addr_w / n_bytes > 1:
                    addr_arg = "int addr"
                    addr_shift = f" + (addr << {int(log(n_bytes, 2))})"
                fsw.write(f"{sw_type} {core_prefix}GET_{name_upper}({addr_arg}) {{\n")
                fsw.write(
                    f"  return (*( (volatile {sw_type} *) ( (base) + ({core_prefix}{name_upper}_ADDR){addr_shift}) ));\n"
                )
                fsw.write("}\n\n")
        fsw.close()

    def write_tbcode(self, table, out_dir, top):
        # Write Verilator code as well
        self.write_verilator_code(table, out_dir, top)

        os.makedirs(out_dir, exist_ok=True)
        fsw = open(f"{out_dir}/{top}_csrs_emb_tb.vs", "w")
        core_prefix = f"{top}_".upper()
        # fsw.write(f'`include "{top}_csrs_def.vh"\n\n')

        fsw.write("\n// CSRS Core Setters and Getters\n")

        for row in table:
            name = row.name.upper()
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if "W" in row.type:
                sw_type = f"[{int(n_bytes*8)}-1:0]"
                addr_arg = ""
                addr_arg = ""
                addr_shift = ""
                if addr_w / n_bytes > 1:
                    addr_arg = ", input reg [ADDR_W-1:0] addr"
                    addr_shift = f" + (addr << {int(log(n_bytes, 2))})"
                fsw.write(
                    f"task static {core_prefix}SET_{name}(input reg {sw_type} value{addr_arg});\n"
                )
                fsw.write(
                    f"  iob_write( (`{core_prefix}{name}_ADDR){addr_shift}, value, `{core_prefix}{name}_W);\n"
                )
                fsw.write("endtask\n\n")
            if "R" in row.type:
                sw_type = f"[{int(n_bytes*8)}-1:0]"
                addr_arg = ""
                addr_shift = ""
                if addr_w / n_bytes > 1:
                    addr_arg = "input reg [ADDR_W-1:0] addr, "
                    addr_shift = f" + (addr << {int(log(n_bytes, 2))})"
                fsw.write(
                    f"task static {core_prefix}GET_{name}({addr_arg}output reg {sw_type} rvalue);\n"
                )
                fsw.write(
                    f"  iob_read( (`{core_prefix}{name}_ADDR){addr_shift}, rvalue, `{core_prefix}{name}_W);\n"
                )
                fsw.write("endtask\n\n")
        fsw.close()

    def write_verilator_code(self, table, out_dir, top):
        self.write_swheader_verilator(table, out_dir, top)
        os.makedirs(out_dir, exist_ok=True)
        fsw = open(f"{out_dir}/{top}_csrs_emb_verilator.c", "w")
        core_prefix = f"{top}_".upper()
        fsw.write(f'#include "{top}_verilator.h"\n\n')

        fsw.write("\n// Core Setters and Getters\n")

        for row in table:
            name = row.name
            name_upper = name.upper()
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if "W" in row.type:
                sw_type = self.csr_type(name, n_bytes)
                addr_arg = ""
                addr_arg = ""
                addr_shift = ""
                if addr_w / n_bytes > 1:
                    addr_arg = ", int addr"
                    addr_shift = f" + (addr << {int(log(n_bytes, 2))})"
                fsw.write(
                    f"void {core_prefix}SET_{name_upper}({sw_type} value{addr_arg}, iob_native_t *native_if) {{\n"
                )
                fsw.write(
                    f"  iob_write(({core_prefix}{name_upper}_ADDR){addr_shift}, value, {core_prefix}{name_upper}_W, native_if);\n"
                )
                fsw.write("}\n\n")
            if "R" in row.type:
                sw_type = self.csr_type(name, n_bytes)
                addr_arg = ""
                addr_shift = ""
                if addr_w / n_bytes > 1:
                    addr_arg = "int addr, "
                    addr_shift = f" + (addr << {int(log(n_bytes, 2))})"
                fsw.write(
                    f"{sw_type} {core_prefix}GET_{name_upper}({addr_arg}iob_native_t *native_if) {{\n"
                )
                fsw.write(
                    f"  return ({sw_type})iob_read(({core_prefix}{name_upper}_ADDR){addr_shift}, native_if);\n"
                )
                fsw.write("}\n\n")
        fsw.close()

    def write_swheader_verilator(self, table, out_dir, top):
        os.makedirs(out_dir, exist_ok=True)
        fswhdr = open(f"{out_dir}/{top}_csrs_verilator.h", "w")

        core_prefix = f"{top}_".upper()

        fswhdr.write(f"#ifndef H_{core_prefix}CSRS_VERILATOR_H\n")
        fswhdr.write(f"#define H_{core_prefix}CSRS_VERILATOR_H\n\n")
        fswhdr.write("#include <stdint.h>\n\n")
        fswhdr.write('#include "iob_tasks.h"\n\n')

        fswhdr.write("//used address space width\n")
        fswhdr.write(f"#define  {core_prefix}CSRS_ADDR_W {self.core_addr_w}\n\n")

        fswhdr.write("//used address space width\n")
        fswhdr.write(f"#define  {core_prefix}CSRS_ADDR_W {self.core_addr_w}\n\n")

        fswhdr.write("//Addresses\n")
        for row in table:
            name = row.name.upper()
            if "W" in row.type or "R" in row.type:
                fswhdr.write(f"#define {core_prefix}{name}_ADDR {row.addr}\n")

        fswhdr.write("\n//Data widths (bit)\n")
        for row in table:
            name = row.name.upper()
            n_bits = row.n_bits
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            if "W" in row.type or "R" in row.type:
                fswhdr.write(f"#define {core_prefix}{name}_W {n_bytes*8}\n")

        # fswhdr.write("\n// Base Address\n")
        # fswhdr.write(f"void {core_prefix}INIT_BASEADDR(uint32_t addr);\n")

        fswhdr.write("\n// Core Setters and Getters\n")
        for row in table:
            name = row.name
            name_upper = name.upper()
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if "W" in row.type:
                sw_type = self.csr_type(name, n_bytes)
                addr_arg = ""
                if addr_w / n_bytes > 1:
                    addr_arg = ", int addr"
                fswhdr.write(
                    f"void {core_prefix}SET_{name_upper}({sw_type} value{addr_arg}, iob_native_t *native_if);\n"
                )
            if "R" in row.type:
                sw_type = self.csr_type(name, n_bytes)
                addr_arg = ""
                if addr_w / n_bytes > 1:
                    addr_arg = "int addr, "
                fswhdr.write(
                    f"{sw_type} {core_prefix}GET_{name_upper}({addr_arg}iob_native_t *native_if);\n"
                )

        fswhdr.write(f"\n#endif // H_{core_prefix}_CSRS_VERILATOR_H\n")

        fswhdr.close()

    # check if address is aligned
    @staticmethod
    def check_alignment(addr, addr_w):
        if addr % (2**addr_w) != 0:
            sys.exit(
                f"{iob_colors.FAIL}address {addr} with span {2**addr_w} is not aligned{iob_colors.ENDC}"
            )

    # check if address overlaps with previous
    @staticmethod
    def check_overlap(addr, addr_type, read_addr, write_addr):
        if addr_type == "R" and addr < read_addr:
            sys.exit(
                f"{iob_colors.FAIL}read address {addr} overlaps with previous addresses{iob_colors.ENDC}"
            )
        elif addr_type == "W" and addr < write_addr:
            sys.exit(
                f"{iob_colors.FAIL}write address {addr} overlaps with previous addresses{iob_colors.ENDC}"
            )

    # check autoaddr configuration
    @staticmethod
    def check_autoaddr(autoaddr, row):
        is_version = row.name == "version"
        if is_version:
            # version has always automatic address
            return -1

        # invalid autoaddr + register addr configurations
        if autoaddr and row.addr > -1:
            sys.exit(
                f"{iob_colors.FAIL}Manual address in register named {row.name} while in auto address mode.{iob_colors.ENDC}"
            )
        if (not autoaddr) and row.addr < 0:
            sys.exit(
                f"{iob_colors.FAIL}Missing address in register named {row.name} while in manual address mode.{iob_colors.ENDC}"
            )

        if autoaddr:
            return -1
        else:
            return row.addr

    # compute address
    def compute_addr(self, table, rw_overlap, autoaddr):
        read_addr = 0
        write_addr = 0

        tmp = []

        for row in table:
            addr = self.check_autoaddr(autoaddr, row)
            addr_type = row.type
            n_bits = row.n_bits
            log2n_items = row.log2n_items
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if addr >= 0:  # manual address
                self.check_alignment(addr, addr_w)
                self.check_overlap(addr, addr_type, read_addr, write_addr)
                addr_tmp = addr
            elif "R" in addr_type:  # auto address
                read_addr = self.bceil(read_addr, addr_w)
                addr_tmp = read_addr
            elif "W" in addr_type:
                write_addr = self.bceil(write_addr, addr_w)
                addr_tmp = write_addr
            else:
                sys.exit(
                    f"{iob_colors.FAIL}invalid address type {addr_type} for register named {row.name}{iob_colors.ENDC}"
                )

            if autoaddr and not rw_overlap:
                addr_tmp = max(read_addr, write_addr)

            # save address temporarily in list
            tmp.append(addr_tmp)

            # update addresses
            addr_tmp += 2**addr_w
            if "R" in addr_type:
                read_addr = addr_tmp
            elif "W" in addr_type:
                write_addr = addr_tmp
            if not rw_overlap:
                read_addr = addr_tmp
                write_addr = addr_tmp

        # update reg addresses
        for i in range(len(tmp)):
            table[i].addr = tmp[i]

        # update core address space size
        self.core_addr_w = int(ceil(log(max(read_addr, write_addr), 2)))

        return table

    # Generate csrs.tex file with list TeX tables of regs
    @staticmethod
    def generate_csrs_tex(regs, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        csrs_file = open(f"{out_dir}/csrs.tex", "w")

        csrs_file.write(
            """
    The software accessible registers of the core are described in the following
    tables. The tables give information on the name, read/write capability, address, width in bits, and a textual description.
"""
        )

        for table in regs:
            csrs_file.write(
                """
    \\begin{table}[H]
      \\centering
      \\begin{tabularx}{\\textwidth}{|l|c|c|c|c|X|}
        
        \\hline
        \\rowcolor{iob-green}
        {\\bf Name} & {\\bf R/W} & {\\bf Addr} & {\\bf Width} & {\\bf Default} & {\\bf Description} \\\\ \\hline

        \\input """
                + table.name
                + """_csrs_tab
     
      \\end{tabularx}
      \\caption{"""
                + table.descr.replace("_", "\\_")
                + """}
      \\label{"""
                + table.name
                + """_csrs_tab:is}
    \\end{table}
    """
            )

        csrs_file.write("\\clearpage")
        csrs_file.close()

    # Generate TeX tables of registers
    # regs: list of tables containing registers, as defined in <corename>_setup.py
    # regs_with_addr: list of all registers, where 'addr' field has already been computed
    # out_dir: output directory
    @classmethod
    def generate_regs_tex(self, regs, regs_with_addr, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        # Create csrs.tex file
        self.generate_csrs_tex(regs, out_dir)

        for table in regs:
            tex_table = []
            for reg in table.regs:
                # Find address of matching register in regs_with_addr list
                addr = next(
                    register.addr
                    for register in regs_with_addr
                    if register.name == reg.name
                )
                tex_table.append(
                    [
                        reg.name,
                        reg.type,
                        str(addr),
                        str(reg.n_bits),
                        str(reg.rst_val),
                        reg.descr,
                    ]
                )

            write_table(f"{out_dir}/{table.name}_csrs", tex_table)
