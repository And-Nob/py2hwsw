# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT

import math

from csr_classes import fail_with_msg


def find_and_update_regfile_csrs(csrs_dict, attributes_dict):
    """Given a dictionary of CSRs, find the regfile CSRs group and update the dictionary
    accordingly.
    User should provide a CSR of type "*REGFILE". This CSR will be replaced by regfile_csrs.
    :param dict csrs_dict: Dictionary of CSRs to update.
    :param dict attributes_dict: Dictionary of core attributes to add regfile instance, wires and ports.
    """
    csr_group_ref = None
    for csr_group in csrs_dict:
        csr_ref = None
        for csr in csr_group["regs"]:
            if csr.get("type", "") in ["REGFILE", "AREGFILE"]:
                csr_group_ref = csr_group
                csr_ref = csr
                break

        if not csr_ref:
            continue

        # Replace original csr with "NOAUTO" type
        csr_ref["type"] = "NOAUTO"
        # Don't generate standard ports for this CSR.
        # It will be internal to the CSRs module, and have a custom port generated later.
        csr_ref["internal_use"] = True

        create_regfile_instance(attributes_dict, csr_ref)


def create_regfile_instance(attributes_dict, csr_ref):
    """Add regfile instance, wires and ports to given attributes_dict, based on regfile description provided by CSR.
    :param dict attributes_dict: Dictionary of core attributes to add regfile instance, wires and ports.
    :param dict csr_ref: CSR description dictionary, with REGFILE information.
    """
    regfile_name = csr_ref["name"]
    REGFILE_NAME = regfile_name.upper()
    mode = csr_ref["mode"]

    log2n_items = csr_ref["log2n_items"]
    n_items = 2**log2n_items
    n_bits = csr_ref["n_bits"]
    asym = csr_ref.get("asym", 1)
    asym_sign = f"iob_sign({asym})"
    internal_n_bits = f"({n_bits} * ({asym}**{asym_sign}))"
    # external_n_bits = "DATA_W"

    wdata_w = n_bits if mode == "W" else internal_n_bits
    rdata_w = n_bits if mode == "R" else internal_n_bits
    waddr_w = (
        log2n_items
        if mode == "W"
        else (f"{log2n_items} + {asym_sign} * $clog2(iob_abs({asym}))")
    )
    raddr_w = (
        log2n_items
        if mode == "R"
        else (f"{log2n_items} + {asym_sign} * $clog2(iob_abs({asym}))")
    )

    #
    # Confs: Based on confs from iob_regarray_2p.py
    #
    # Create confs to simplify long expressions.
    attributes_dict["confs"] += [
        {
            "name": f"{REGFILE_NAME}_W_DATA_W",
            "descr": "",
            "type": "D",
            "val": wdata_w,
            "min": "NA",
            "max": "NA",
        },
        {
            "name": f"{REGFILE_NAME}_R_DATA_W",
            "descr": "",
            "type": "D",
            "val": rdata_w,
            "min": "NA",
            "max": "NA",
        },
        {
            "name": f"{REGFILE_NAME}_W_ADDR_W",
            "descr": "Write address width",
            "type": "D",
            "val": waddr_w,
            "min": "NA",
            "max": "NA",
        },
        {
            "name": f"{REGFILE_NAME}_R_ADDR_W",
            "descr": "Read address width",
            "type": "D",
            "val": raddr_w,
            "min": "NA",
            "max": "NA",
        },
    ]
    #
    # Ports
    # #TODO:
    attributes_dict["ports"].append(
        {
            "name": f"{regfile_name}_rst_i",
            "descr": "Synchronous reset interface.",
            "signals": [
                {
                    "name": f"{regfile_name}_rst_i",
                    "width": 1,
                    "descr": "Synchronous reset input",
                },
            ],
        }
    )
    if mode == "R":
        attributes_dict["ports"] += [
            {
                "name": f"{regfile_name}_write_io",
                "descr": "REGFILE write interface.",
                "signals": [
                    {
                        "name": f"{regfile_name}_w_en_i",
                        "width": 1,
                        "descr": "Write enable",
                    },
                    {
                        "name": f"{regfile_name}_w_data_i",
                        "width": f"{REGFILE_NAME}_W_DATA_W",
                        "descr": "Write data",
                    },
                    {
                        "name": f"{regfile_name}_w_full_o",
                        "width": 1,
                        "descr": "Write full signal",
                    },
                ],
            },
            {
                "name": f"{regfile_name}_interrupt_o",
                "descr": "Connects directly to REGFILE",
                "signals": [
                    {
                        "name": f"{regfile_name}_interrupt_o",
                        "width": 1,
                        "descr": "REGFILE interrupt. Active when level reaches threshold.",
                    },
                ],
            },
        ]
    else:  # mode == "W"
        attributes_dict["ports"].append(
            {
                "name": f"{regfile_name}_read_io",
                "descr": "REGFILE read interface.",
                "signals": [
                    {
                        "name": f"{regfile_name}_r_en_i",
                        "width": 1,
                        "descr": "Read enable",
                    },
                    {
                        "name": f"{regfile_name}_r_data_o",
                        "width": f"{REGFILE_NAME}_R_DATA_W",
                        "descr": "Read data",
                    },
                    {
                        "name": f"{regfile_name}_r_empty_o",
                        "width": 1,
                        "descr": "Read empty signal",
                    },
                ],
            }
        )
    attributes_dict["ports"] += [
        {
            "name": f"{regfile_name}_extmem_io",
            "descr": "REGFILE external memory interface.",
            "signals": [
                {
                    "name": f"{regfile_name}_ext_mem_clk_o",
                    "width": 1,
                },
                {
                    "name": f"{regfile_name}_ext_mem_w_en_o",
                    "width": f"{REGFILE_NAME}_R",
                    "descr": "Memory write enable",
                },
                {
                    "name": f"{regfile_name}_ext_mem_w_addr_o",
                    "width": f"{REGFILE_NAME}_MINADDR_W",
                    "descr": "Memory write address",
                },
                {
                    "name": f"{regfile_name}_ext_mem_w_data_o",
                    "width": f"{REGFILE_NAME}_MAXDATA_W",
                    "descr": "Memory write data",
                },
                #  Read port
                {
                    "name": f"{regfile_name}_ext_mem_r_en_o",
                    "width": f"{REGFILE_NAME}_R",
                    "descr": "Memory read enable",
                },
                {
                    "name": f"{regfile_name}_ext_mem_r_addr_o",
                    "width": f"{REGFILE_NAME}_MINADDR_W",
                    "descr": "Memory read address",
                },
                {
                    "name": f"{regfile_name}_ext_mem_r_data_i",
                    "width": f"{REGFILE_NAME}_MAXDATA_W",
                    "descr": "Memory read data",
                },
            ],
        },
        {
            "name": f"{regfile_name}_current_level_o",
            "descr": "Connects directly to REGFILE",
            "signals": [
                {
                    "name": f"{regfile_name}_current_level_o",
                    "width": f"{REGFILE_NAME}_ADDR_W+1",
                    "descr": "REGFILE level",
                },
            ],
        },
    ]
    attributes_dict["wires"] += []
    #
    # Wires
    # #TODO:
    if mode == "W":
        attributes_dict["wires"].append(
            {
                "name": f"{regfile_name}_write_io",
                "descr": "REGFILE write interface.",
                "signals": [
                    {"name": f"{regfile_name}_data_wen", "width": 1},
                    {"name": f"{regfile_name}_wdata", "width": 32},
                    {"name": f"{regfile_name}_full", "width": 1},
                ],
            }
        )
    else:  # mode == "R"
        attributes_dict["wires"].append(
            {
                "name": f"{regfile_name}_read_io",
                "descr": "REGFILE read interface.",
                "signals": [
                    {"name": f"{regfile_name}_data_ren", "width": 1},
                    {"name": f"{regfile_name}_data_rdata", "width": 32},
                    {"name": f"{regfile_name}_empty", "width": 1},
                ],
            }
        )
    #
    # Blocks
    #
    attributes_dict["subblocks"].append(
        {
            "core_name": "iob_regarray_2p",
            "instance_name": regfile_name,
            "instance_description": f"REGFILE {regfile_name}",
            "parameters": {
                "N": n_items,  # number of registers
                "W": n_bits,  # register width
                "WDATA_W": f"{REGFILE_NAME}_W_DATA_W",  # width of write data
                "WADDR_W": f"{REGFILE_NAME}_W_ADDR_W",  # width of write address
                "RDATA_W": f"{REGFILE_NAME}_R_DATA_W",  # width of read data
                "RADDR_W": f"{REGFILE_NAME}_R_ADDR_W",  # width of read address
                "DATA_W": "DATA_W",  # width of data
            },
            "connect": {
                "clk_en_rst_s": "clk_en_rst_s",
                "rst_i": f"{regfile_name}_rst_i",
                "write_io": f"{regfile_name}_write_io",
                "read_io": f"{regfile_name}_read_io",
                "extmem_io": f"{regfile_name}_extmem_io",
                "regfile_o": f"{regfile_name}_current_level_o",
            },
        }
    )
    #
    # Snippets
    #

    attributes_dict["snippets"].append(
        {  # TODO:
            "verilog_code": f"""
// Connect REGFILE level status to CSRs
assign {regfile_name}_level = {regfile_name}_current_level_o;

""",
        }
    )
