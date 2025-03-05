# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT

import copy
import os
import math
from latex import write_table
from iob_base import find_obj_in_list


def setup(py_params_dict):
    """Memory wrapper core. Inteended to be used as a superblock of other cores.
    Required memories are automatically generated based on the ports of the instantiator (subblock).
    """

    # List of supported memory interfaces (usually taken from if_gen.py)
    mem_if_names = py_params_dict["mem_if_names"]
    attrs = py_params_dict["instantiator"]

    attributes_dict = {
        "name": f"{attrs['name']}_mwrap",
        "generate_hw": True,
        "confs": attrs["confs"]
        + [
            {
                "name": "MEM_NO_READ_ON_WRITE",
                "type": "P",
                "val": "0",
                "min": "0",
                "max": "1",
                "descr": "No simultaneous read/write",
            },
        ],
    }

    mwrap_wires = []
    mwrap_ports = []
    for port in attrs["ports"]:
        if isinstance(port["signals"], dict):
            if port["signals"]["type"] in mem_if_names:
                wire = copy.deepcopy(port)
                mwrap_wires.append(wire)
            else:
                mwrap_ports.append(port)
        else:
            mwrap_ports.append(port)

    attributes_dict["ports"] = mwrap_ports

    attributes_dict["wires"] = mwrap_wires

    attributes_dict["subblocks"] = [
        {
            "core_name": attrs["original_name"],
            "instance_name": f"{attrs['name']}_inst",
            "instance_description": "Wrapped module",
            "parameters": {
                i["name"]: i["name"] for i in attrs["confs"] if i["type"] in ["P", "F"]
            },
            "connect": {i["name"]: i["name"] for i in attrs["ports"]},
        }
    ]

    list_of_mems = []
    for wire in mwrap_wires:
        if wire["signals"].get("prefix", None):
            prefix_str = wire["signals"]["prefix"]
        else:
            prefix_str = wire["name"] + "_"

        # Word address bus width
        word_addr_w = wire["signals"].get("ADDR_W", 32)
        # Data bus width
        data_w = wire["signals"].get("DATA_W", 32)

        hexfile_param = f"{prefix_str.upper()}HEXFILE"
        list_of_mems.append(
            {
                "name": f"{prefix_str}mem",
                "type": f"iob_{wire['signals']['type']}",
                # Get default values of parameters
                "addr_w": word_addr_w,
                "data_w": data_w,
                "hexfile": find_obj_in_list(attrs["confs"], hexfile_param)["val"],
            }
        )

        # Extra Verilog parameters for this memory subblock
        extra_params = {}
        if "ram" in list_of_mems[-1]["type"]:
            extra_params["MEM_NO_READ_ON_WRITE"] = "MEM_NO_READ_ON_WRITE"

        attributes_dict["subblocks"].append(
            {
                "core_name": list_of_mems[-1]["type"],
                "instance_name": list_of_mems[-1]["name"],
                "parameters": {
                    "DATA_W": data_w,
                    "ADDR_W": word_addr_w,
                    "HEXFILE": hexfile_param,
                }
                | extra_params,
                "connect": {
                    f"{wire['signals']['type']}_s": wire["name"],
                },
            }
        )

    if "superblocks" in attrs:
        attributes_dict["superblocks"] = attrs["superblocks"]

    # Generate LaTeX table of memories
    # But don't create files for other targets (like clean)
    if py_params_dict.get("py2hwsw_target", "") == "setup":
        assert py_params_dict["build_dir"], "[iob_memwrapper]: Error: build_dir not set"
        generate_mems_tex(
            list_of_mems, os.path.join(py_params_dict["build_dir"], "document/tsrc")
        )

    return attributes_dict


#
# Document functions
#


# Generate mems.tex file with list TeX tables of mems
def generate_mems_tex(mems, out_dir):
    """Generate TeX for memories section
    :param mems: list of memories
    :param out_dir: output directory
    """
    os.makedirs(out_dir, exist_ok=True)
    mems_file = open(f"{out_dir}/mems.tex", "w")

    mems_file.write(
        """
    The memories of the core are described in the following table.
    The tables give information on the name, type, address and data width in bits, and initialization file name.
"""
    )

    mems_file.write(
        """
    \\begin{table}[H]
      \\centering
      \\begin{tabularx}{\\textwidth}{|l|c|c|c|X|}
        \\hline
        \\rowcolor{iob-green}
        {\\bf Name} & {\\bf Type} & {\\bf (Word-)Addr Width} & {\\bf Data Width} & {\\bf Init file} \\\\ \\hline
        \\input mems_tab
      \\end{tabularx}
      \\caption{Table of memories of the core}
      \\label{mems_tab:is}
    \\end{table}
"""
    )

    mems_file.write("\\clearpage")
    mems_file.close()

    # Generate mems table
    tex_table = []
    for mem in mems:
        tex_table.append(
            [
                mem["name"],
                mem["type"],
                str(mem["addr_w"]),
                str(mem["data_w"]),
                mem["hexfile"],
            ]
        )

    write_table(f"{out_dir}/mems", tex_table)
