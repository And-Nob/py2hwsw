#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 IObundle
#
# SPDX-License-Identifier: MIT

import os
import re

from latex import write_table


def conf_vh(macros, top_module, out_dir):
    file2create = open(f"{out_dir}/{top_module}_conf.vh", "w")
    core_prefix = f"{top_module}_".upper()
    fname = f"{core_prefix}CONF"
    # These ifndefs cause issues when this file is included in multiple files and it contains other ifdefs inside this block.
    # For example, assume this file is included in another one that does not have `MACRO1` defined. Now assume that inside this block there is an `ifdef MACRO1` block.
    # Since `MACRO1` is not defined in the file that is including this, the `ifdef MACRO1` wont be executed.
    # Now assume this file is included in another file that has `MACRO1` defined. Now, this block
    # wont execute because of the `ifndef` added here, therefore the `ifdef MACRO1` block will also not execute when it should have.
    # file2create.write(f"`ifndef VH_{fname}_VH\n")
    # file2create.write(f"`define VH_{fname}_VH\n\n")
    for macro in macros:
        # If macro has 'doc_only' attribute set to True, skip it
        if macro.doc_only:
            continue
        if macro.if_defined:
            file2create.write(f"`ifdef {macro.if_defined}\n")
        if macro.if_not_defined:
            file2create.write(f"`ifndef {macro.if_not_defined}\n")
        # Only insert macro if its is not a bool define, and if so only insert it if it is true
        if type(macro.val) is not bool:
            m_name = macro.name.upper()
            m_default_val = macro.val
            file2create.write(f"`define {core_prefix}{m_name} {m_default_val}\n")
        elif macro.val:
            m_name = macro.name.upper()
            file2create.write(f"`define {core_prefix}{m_name} 1\n")
        if macro.if_defined or macro.if_not_defined:
            file2create.write("`endif\n")
    # file2create.write(f"\n`endif // VH_{fname}_VH\n")


def conf_h(macros, top_module, out_dir):
    if len(macros) == 0:
        return
    os.makedirs(out_dir, exist_ok=True)
    file2create = open(f"{out_dir}/{top_module}_conf.h", "w")
    core_prefix = f"{top_module}_".upper()
    fname = f"{core_prefix}CONF"
    file2create.write(f"#ifndef H_{fname}_H\n")
    file2create.write(f"#define H_{fname}_H\n\n")
    for macro in macros:
        # If macro has 'doc_only' attribute set to True, skip it
        if macro.doc_only:
            continue
        # Only insert macro if its is not a bool define, and if so only insert it if it is true
        if type(macro.val) is not bool:
            m_name = macro.name.upper()
            # Replace any Verilog specific syntax by equivalent C syntax
            m_default_val = re.sub("\\d+'h", "0x", str(macro.val))
            m_min_val = re.sub("\\d+'h", "0x", str(macro.min))
            m_max_val = re.sub("\\d+'h", "0x", str(macro.max))
            file2create.write(
                f"#define {core_prefix}{m_name} {str(m_default_val).replace('`', '')}\n"
            )  # Remove Verilog macros ('`')
            file2create.write(
                f"#define {core_prefix}{m_name}_MIN {str(m_min_val).replace('`', '')}\n"
            )  # Remove Verilog macros ('`')
            file2create.write(
                f"#define {core_prefix}{m_name}_MAX {str(m_max_val).replace('`', '')}\n"
            )  # Remove Verilog macros ('`')
        elif macro.val:
            m_name = macro.name.upper()
            file2create.write(f"#define {core_prefix}{m_name} 1\n")
    file2create.write(f"\n#endif // H_{fname}_H\n")

    file2create.close()


def config_build_mk(python_module):
    file2create = open(f"{python_module.build_dir}/config_build.mk", "w")
    file2create.write(f"NAME={python_module.name}\n")
    file2create.write("CSR_IF ?=iob\n")
    file2create.write(f"BUILD_DIR_NAME={python_module.build_dir.split('/')[-1]}\n")
    file2create.write(f"IS_FPGA={int(python_module.is_system)}\n")

    file2create.close()


# Append a string to the config_build.mk
def append_str_config_build_mk(str_2_append, build_dir):
    file = open(f"{build_dir}/config_build.mk", "a")
    file.write(str_2_append)
    file.close()


# Generate TeX table of confs
def generate_confs_tex(confs, out_dir):
    tex_table = []
    derv_params = []
    for conf in confs:
        conf_val = conf.val if type(conf.val) is not bool else "1"
        # False parameters are not included in the table
        if conf.type != "F":
            tex_table.append(
                [
                    conf.name,
                    conf.type,
                    conf.min,
                    conf_val,
                    conf.max,
                    conf.descr,
                ]
            )
        else:
            derv_params.append(
                [
                    conf.name,
                    conf_val,
                    conf.descr,
                ]
            )

    # Write table with true parameters and macros
    write_table(f"{out_dir}/confs", tex_table)


# Select if a define from the confs dictionary is set or not
# define_name: name of the macro in confs (its called define because it is unvalued, it is either set or unset)
# should_set: Select if define should be set or not
def update_define(confs, define_name, should_set):
    for macro in confs:
        if macro.name == define_name:
            # Found macro. Unset it if not 'should_set'
            if should_set:
                macro.val = True
            else:
                macro.val = False
            break
    else:
        # Did not find define. Set it if should_set.
        if should_set:
            confs.append(
                {
                    "name": define_name,
                    "type": "M",
                    "val": True,
                    "min": "NA",
                    "max": "NA",
                    "descr": "Define",
                }
            )


def generate_confs(core):
    conf_vh(
        core.confs,
        core.name,
        os.path.join(core.build_dir, core.dest_dir),
    )
    conf_h(core.confs, core.name, core.build_dir + "/software/include")
