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
                "interface": {
                    "type": "clk_en_rst",
                },
                "descr": "Clock, clock enable and reset",
            },
            {
                "name": "apb_s",
                "interface": {
                    "type": "apb",
                },
                "descr": "APB interface",
            },
            {
                "name": "iob_m",
                "interface": {
                    "type": "iob",
                },
                "descr": "CPU native interface",
            },
        ],
        "blocks": [
            {
                "core_name": "iob_reg_e",
                "instance_name": "iob_reg_e_inst",
            },
        ],
    }

    return attributes_dict
