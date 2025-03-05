# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT


def setup(py_params_dict):
    attributes_dict = {
        "generate_hw": False,
        "ports": [
            {
                "name": "clk_en_rst_s",
                "signals": {
                    "type": "iob_clk",
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
                "name": "config_in_io",
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
                "name": "config_out_io",
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
                "name": "axis_in_io",
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
                "name": "axis_out_io",
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
                "name": "extmem_io",
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
            # Not real ports of iob_axis2axi
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
        "subblocks": [
            {
                "core_name": "iob_axis2axi_in",
            },
            {
                "core_name": "iob_axis2axi_out",
            },
            # For simulation
            {
                "core_name": "iob_axi_ram",
                "dest_dir": "hardware/simulation/src",
            },
            {
                "core_name": "iob_ram_t2p_be",
                "dest_dir": "hardware/simulation/src",
            },
            {
                "core_name": "iob_ram_at2p",
                "dest_dir": "hardware/simulation/src",
            },
        ],
    }

    return attributes_dict
