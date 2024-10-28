# SPDX-FileCopyrightText: 2024 IObundle
#
# SPDX-License-Identifier: MIT


def setup(py_params_dict):
    attributes_dict = {
        "version": "0.1",
        "generate_hw": False,
        "ports": [
            {
                "name": "clk_en_rst_s",
                "signals": {
                    "type": "clk_en_rst",
                },
                "descr": "Clock, clock enable and reset",
            },
            {
                "name": "rst_i",
                "descr": "Synchronous reset interface",
                "signals": [
                    {
                        "name": "rst_i",
                        "width": 1,
                        "descr": "Synchronous reset input",
                    },
                ],
            },
            {
                "name": "config_in",
                "descr": "AXI Stream input configuration interface",
                "signals": [
                    {
                        "name": "config_in_addr_i",
                        "width": "ADDR_W",
                        "descr": "",
                    },
                    {
                        "name": "config_in_valid_i",
                        "width": 1,
                        "descr": "",
                    },
                    {
                        "name": "config_in_ready_o",
                        "width": 1,
                        "descr": "",
                    },
                ],
            },
            {
                "name": "config_out",
                "descr": "AXI Stream output configuration interface",
                "signals": [
                    {
                        "name": "config_out_addr_i",
                        "width": "ADDR_W",
                        "descr": "",
                    },
                    {
                        "name": "config_out_length_i",
                        "width": "ADDR_W",
                        "descr": "",
                    },
                    {
                        "name": "config_out_valid_i",
                        "width": 1,
                        "descr": "",
                    },
                    {
                        "name": "config_out_ready_o",
                        "width": 1,
                        "descr": "",
                    },
                ],
            },
            {
                "name": "axis_in",
                "descr": "AXI Stream input interface",
                "signals": [
                    {
                        "name": "axis_in_data_i",
                        "width": "DATA_W",
                        "descr": "",
                    },
                    {
                        "name": "axis_in_valid_i",
                        "width": 1,
                        "descr": "",
                    },
                    {
                        "name": "axis_in_ready_o",
                        "width": 1,
                        "descr": "",
                    },
                ],
            },
            {
                "name": "axis_out",
                "descr": "AXI Stream output interface",
                "signals": [
                    {
                        "name": "axis_out_data_o",
                        "width": "DATA_W",
                        "descr": "",
                    },
                    {
                        "name": "axis_out_valid_o",
                        "width": 1,
                        "descr": "",
                    },
                    {
                        "name": "axis_out_ready_i",
                        "width": 1,
                        "descr": "",
                    },
                ],
            },
            {
                "name": "axi_m",
                "signals": {
                    "type": "axi",
                    "ADDR_W": "ADDR_W",
                    "DATA_W": "DATA_W",
                },
                "descr": "AXI master interface",
            },
            {
                "name": "extmem",
                "descr": "External memory interface",
                "signals": [
                    {
                        "name": "ext_mem_w_en_o",
                        "width": 1,
                        "descr": "Memory write enable",
                    },
                    {
                        "name": "ext_mem_w_addr_o",
                        "width": "BUFFER_W",
                        "descr": "Memory write address",
                    },
                    {
                        "name": "ext_mem_w_data_o",
                        "width": "DATA_W",
                        "descr": "Memory write data",
                    },
                    {
                        "name": "ext_mem_r_en_o",
                        "width": 1,
                        "descr": "Memory read enable",
                    },
                    {
                        "name": "ext_mem_r_addr_o",
                        "width": "BUFFER_W",
                        "descr": "Memory read address",
                    },
                    {
                        "name": "ext_mem_r_data_i",
                        "width": "DATA_W",
                        "descr": "Memory read data",
                    },
                ],
            },
            # Not real ports of axis2axi
            # {
            #     "name": "axi_write",
            #     "descr": "AXI write interface",
            #     "signals": [],
            # },
            # {
            #     "name": "axi_read",
            #     "descr": "AXI read interface",
            #     "signals": [],
            # },
        ],
        "blocks": [
            {
                "core_name": "iob_fifo_sync",
                "instance_name": "iob_fifo_sync_inst",
            },
            {
                "core_name": "iob_counter",
                "instance_name": "iob_counter_inst",
            },
            {
                "core_name": "iob_reg_r",
                "instance_name": "iob_reg_r_inst",
            },
            {
                "core_name": "iob_reg_re",
                "instance_name": "iob_reg_re_inst",
            },
            # For simulation
            {
                "core_name": "axi_ram",
                "instance_name": "axi_ram_inst",
            },
            {
                "core_name": "iob_ram_at2p",
                "instance_name": "iob_ram_at2p_inst",
            },
            {
                "core_name": "axis2axi_in",
                "instance_name": "axis2axi_in_inst",
            },
            {
                "core_name": "axis2axi_out",
                "instance_name": "axis2axi_out_inst",
            },
            # Simulation wrapper
            {
                "core_name": "iob_sim",
                "instance_name": "iob_sim",
                "instantiate": False,
                "dest_dir": "hardware/simulation/src",
            },
        ],
    }

    return attributes_dict
