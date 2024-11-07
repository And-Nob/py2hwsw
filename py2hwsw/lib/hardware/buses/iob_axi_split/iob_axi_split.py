# SPDX-FileCopyrightText: 2024 IObundle
#
# SPDX-License-Identifier: MIT

# FIXME: According to AXI, this core should support simultaneous read and write transactions


def setup(py_params_dict):
    assert "name" in py_params_dict, print(
        "Error: Missing name for generated split module."
    )
    assert "num_outputs" in py_params_dict, print(
        "Error: Missing number of outputs for generated split module."
    )

    NUM_OUTPUTS = int(py_params_dict["num_outputs"])
    # Number of bits required for output selection
    NBITS = (NUM_OUTPUTS - 1).bit_length()

    ADDR_W = int(py_params_dict["addr_w"]) if "addr_w" in py_params_dict else 32
    DATA_W = int(py_params_dict["data_w"]) if "data_w" in py_params_dict else 32
    ID_W = int(py_params_dict["id_w"]) if "id_w" in py_params_dict else 1
    SIZE_W = int(py_params_dict["size_w"]) if "size_w" in py_params_dict else 3
    BURST_W = int(py_params_dict["burst_w"]) if "burst_w" in py_params_dict else 2
    LOCK_W = int(py_params_dict["lock_w"]) if "lock_w" in py_params_dict else 2
    CACHE_W = int(py_params_dict["cache_w"]) if "cache_w" in py_params_dict else 4
    PROT_W = int(py_params_dict["prot_w"]) if "prot_w" in py_params_dict else 3
    QOS_W = int(py_params_dict["qos_w"]) if "qos_w" in py_params_dict else 4
    RESP_W = int(py_params_dict["resp_w"]) if "resp_w" in py_params_dict else 2
    LEN_W = int(py_params_dict["len_w"]) if "len_w" in py_params_dict else 8
    DATA_SECTION_W = (
        int(py_params_dict["data_section_w"])
        if "data_section_w" in py_params_dict
        else 8
    )

    axi_signals = [
        # AXI-Lite Write
        ("axi_awaddr", "output", ADDR_W),
        ("axi_awprot", "output", PROT_W),
        ("axi_awvalid", "output", 1),
        ("axi_awready", "input", 1),
        ("axi_wdata", "output", DATA_W),
        ("axi_wstrb", "output", int(DATA_W / DATA_SECTION_W)),
        ("axi_wvalid", "output", 1),
        ("axi_wready", "input", 1),
        ("axi_bresp", "input", RESP_W),
        ("axi_bvalid", "input", 1),
        ("axi_bready", "output", 1),
        # AXI specific write
        ("axi_awid", "output", ID_W),
        ("axi_awlen", "output", LEN_W),
        ("axi_awsize", "output", SIZE_W),
        ("axi_awburst", "output", BURST_W),
        ("axi_awlock", "output", LOCK_W),
        ("axi_awcache", "output", CACHE_W),
        ("axi_awqos", "output", QOS_W),
        ("axi_wlast", "output", 1),
        ("axi_bid", "input", ID_W),
        # AXI-Lite Read
        ("axi_araddr", "output", ADDR_W),
        ("axi_arprot", "output", PROT_W),
        ("axi_arvalid", "output", 1),
        ("axi_arready", "input", 1),
        ("axi_rdata", "input", DATA_W),
        ("axi_rresp", "input", RESP_W),
        ("axi_rvalid", "input", 1),
        ("axi_rready", "output", 1),
        # AXI specific read
        ("axi_arid", "output", ID_W),
        ("axi_arlen", "output", LEN_W),
        ("axi_arsize", "output", SIZE_W),
        ("axi_arburst", "output", BURST_W),
        ("axi_arlock", "output", LOCK_W),
        ("axi_arcache", "output", CACHE_W),
        ("axi_arqos", "output", QOS_W),
        ("axi_rid", "input", ID_W),
        ("axi_rlast", "input", 1),
    ]

    attributes_dict = {
        "name": py_params_dict["name"],
        "version": "0.1",
    }
    #
    # Ports
    #
    attributes_dict["ports"] = [
        {
            "name": "clk_en_rst_s",
            "signals": {
                "type": "clk_en_rst",
            },
            "descr": "Clock, clock enable and async reset",
        },
        {
            "name": "reset_i",
            "descr": "Reset signal",
            "signals": [
                {
                    "name": "rst_i",
                    "width": "1",
                },
            ],
        },
        {
            "name": "input_s",
            "signals": {
                "type": "axi",
                "file_prefix": py_params_dict["name"] + "_input_",
                "prefix": "input_",
                "DATA_W": DATA_W,
                "ADDR_W": ADDR_W,
                "ID_W": ID_W,
                "SIZE_W": SIZE_W,
                "BURST_W": BURST_W,
                "LOCK_W": LOCK_W,
                "CACHE_W": CACHE_W,
                "PROT_W": PROT_W,
                "QOS_W": QOS_W,
                "RESP_W": RESP_W,
                "LEN_W": LEN_W,
            },
            "descr": "Split input",
        },
    ]
    for port_idx in range(NUM_OUTPUTS):
        attributes_dict["ports"].append(
            {
                "name": f"output_{port_idx}_m",
                "signals": {
                    "type": "axi",
                    "file_prefix": f"{py_params_dict['name']}_output{port_idx}_",
                    "prefix": f"output{port_idx}_",
                    "DATA_W": DATA_W,
                    "ADDR_W": ADDR_W - NBITS,
                    "ID_W": ID_W,
                    "SIZE_W": SIZE_W,
                    "BURST_W": BURST_W,
                    "LOCK_W": LOCK_W,
                    "CACHE_W": CACHE_W,
                    "PROT_W": PROT_W,
                    "QOS_W": QOS_W,
                    "RESP_W": RESP_W,
                    "LEN_W": LEN_W,
                },
                "descr": "Split output interface",
            },
        )
    #
    # Wires
    #
    attributes_dict["wires"] = [
        # Output selection signals
        {
            "name": "sel_reg_en_rst",
            "descr": "Enable and reset signal for sel_reg",
            "signals": [
                {"name": "sel_reg_en", "width": 1},
                {"name": "rst_i"},
            ],
        },
        {
            "name": "sel_reg_data_i",
            "descr": "Input of sel_reg",
            "signals": [
                {"name": "sel", "width": NBITS},
            ],
        },
        {
            "name": "sel_reg_data_o",
            "descr": "Output of sel_reg",
            "signals": [
                {"name": "sel_reg", "width": NBITS},
            ],
        },
        {
            "name": "output_sel",
            "descr": "Select output interface",
            "signals": [
                {"name": "sel"},
            ],
        },
        {
            "name": "output_sel_reg",
            "descr": "Registered select output interface",
            "signals": [
                {"name": "sel_reg"},
            ],
        },
    ]
    # Generate wires for muxers and demuxers
    for signal, direction, width in axi_signals:
        if direction == "input":
            # Demux signals
            attributes_dict["wires"] += [
                {
                    "name": "demux_" + signal + "_i",
                    "descr": f"Input of {signal} demux",
                    "signals": [
                        {
                            "name": "input_" + signal,
                        },
                    ],
                },
                {
                    "name": "demux_" + signal + "_o",
                    "descr": f"Output of {signal} demux",
                    "signals": [
                        {
                            "name": "demux_" + signal,
                            "width": NUM_OUTPUTS * width,
                        },
                    ],
                },
            ]
        else:  # output direction
            # Mux signals
            attributes_dict["wires"] += [
                {
                    "name": "mux_" + signal + "_i",
                    "descr": f"Input of {signal} demux",
                    "signals": [
                        {
                            "name": "mux_" + signal,
                            "width": NUM_OUTPUTS * width,
                        },
                    ],
                },
                {
                    "name": "mux_" + signal + "_o",
                    "descr": f"Output of {signal} demux",
                    "signals": [
                        {
                            "name": "input_" + signal,
                        },
                    ],
                },
            ]
    #
    # Blocks
    #
    attributes_dict["blocks"] = [
        {
            "core_name": "iob_reg_re",
            "instance_name": "sel_reg_re",
            "parameters": {
                "DATA_W": NBITS,
                "RST_VAL": f"{NBITS}'b0",
            },
            "connect": {
                "clk_en_rst_s": "clk_en_rst_s",
                "en_rst_i": "sel_reg_en_rst",
                "data_i": "sel_reg_data_i",
                "data_o": "sel_reg_data_o",
            },
        },
    ]
    # Generate muxers and demuxers
    for signal, direction, width in axi_signals:
        if direction == "input":
            # Demuxers
            attributes_dict["blocks"].append(
                {
                    "core_name": "iob_demux",
                    "instance_name": "iob_demux_" + signal,
                    "parameters": {
                        "DATA_W": width,
                        "N": NUM_OUTPUTS,
                    },
                    "connect": {
                        "sel_i": "output_sel",
                        "data_i": "demux_" + signal + "_i",
                        "data_o": "demux_" + signal + "_o",
                    },
                },
            )
        else:  # output direction
            # Muxers
            attributes_dict["blocks"].append(
                {
                    "core_name": "iob_mux",
                    "instance_name": "iob_mux_" + signal,
                    "parameters": {
                        "DATA_W": width,
                        "N": NUM_OUTPUTS,
                    },
                    "connect": {
                        "sel_i": "output_sel_reg",
                        "data_i": "mux_" + signal + "_i",
                        "data_o": "mux_" + signal + "_o",
                    },
                },
            )
    #
    # Snippets
    #
    attributes_dict["snippets"] = [
        {
            # Extract output selection bits from address
            "verilog_code": f"""
   assign sel = input_axi_arvalid_i ? input_axi_araddr_i[{ADDR_W-1}-:{NBITS}] : input_axi_awaddr_i[{ADDR_W-1}-:{NBITS}];
   assign sel_reg_en = input_axi_arvalid_i | input_axi_awvalid_i;
""",
        },
    ]

    verilog_code = ""
    # Connect address signal
    for port_idx in range(NUM_OUTPUTS):
        verilog_code += f"""
   assign output{port_idx}_axi_araddr_o = demux_axi_araddr[{port_idx*ADDR_W}+:{ADDR_W-NBITS}];
   assign output{port_idx}_axi_awaddr_o = demux_axi_awaddr[{port_idx*ADDR_W}+:{ADDR_W-NBITS}];
"""
    # Connect other signals
    for signal, direction, width in axi_signals:
        if signal in ["axi_araddr", "axi_awaddr"]:
            continue

        if direction == "input":
            # Connect demuxers outputs
            for port_idx in range(NUM_OUTPUTS):
                verilog_code += f"""
   assign output{port_idx}_{signal}_o = demux_{signal}[{port_idx*width}+:{width}];
"""
        else:  # Output direction
            # Connect muxer inputs
            verilog_code += f"    assign mux_{signal} = {{"
            for port_idx in range(NUM_OUTPUTS - 1, -1, -1):
                verilog_code += f"output{port_idx}_{signal}_i, "
            verilog_code = verilog_code[:-2] + "};\n"
    # Create snippet with muxer and demuxer connections
    attributes_dict["snippets"] += [
        {
            "verilog_code": verilog_code,
        },
    ]

    return attributes_dict
