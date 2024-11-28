# SPDX-FileCopyrightText: 2024 IObundle
#
# SPDX-License-Identifier: MIT

#
#    blocks_gen.py: instantiate Verilog modules and generate their documentation
#

from latex import write_table

import iob_colors
from iob_base import fail_with_msg
from iob_signal import get_real_signal
import param_gen


# Generate blocks.tex file with TeX table of blocks (Verilog modules instances)
def generate_blocks_table_tex(blocks, out_dir):
    blocks_file = open(f"{out_dir}/blocks.tex", "w")

    blocks_file.write(
        "The Verilog modules in the top-level entity of the core are \
        described in the following tables. The table elements represent \
        the blocks in the Block Diagram.\n"
    )

    for group in blocks:
        blocks_file.write(
            """
\\begin{table}[H]
  \\centering
  \\begin{tabularx}{\\textwidth}{|l|l|X|}

    \\hline
    \\rowcolor{iob-green}
    {\\bf Module} & {\\bf Name} & {\\bf Description}  \\\\ \\hline \\hline

    \\input """
            + group.name
            + """_blocks_tab

  \\end{tabularx}
  \\caption{"""
            + group.descr.replace("_", "\\_")
            + """}
  \\label{"""
            + group.name
            + """_blocks_tab:is}
\\end{table}
"""
        )
        if group.doc_clearpage:
            blocks_file.write("\\clearpage")

    blocks_file.write("\\clearpage")
    blocks_file.close()


# Generate TeX table of blocks
def generate_blocks_tex(blocks, out_dir):
    # Create blocks.tex file
    generate_blocks_table_tex(blocks, out_dir)

    # Create table for each group
    for group in blocks:
        tex_table = []
        for block in group.blocks:
            if not block.instantiate:
                continue
            tex_table.append(
                [
                    block.name,
                    block.instance_name,
                    block.instance_description,
                ]
            )

        write_table(f"{out_dir}/{group.name}_blocks", tex_table)


def generate_blocks(core):
    """Generate verilog code with verilog instances of this module.
    returns: Generated verilog code
    """
    code = ""
    for group in core.blocks:
        for instance in group.blocks:
            if not instance.instantiate:
                continue
            # Open ifdef if conditional interface
            if instance.if_defined:
                code += f"`ifdef {instance.if_defined}\n"
            if instance.if_not_defined:
                code += f"`ifndef {instance.if_not_defined}\n"

            params_str = ""
            if instance.parameters:
                params_str = f"""#(
{param_gen.generate_inst_params(instance)}\
    ) """

            code += f"""\
        // {instance.instance_description}
        {instance.name} {params_str}{instance.instance_name} (
    {get_instance_port_connections(instance)}\
        );

    """
            # Close ifdef if conditional interface
            if instance.if_defined or instance.if_not_defined:
                code += "`endif\n"

    return code


def generate_blocks_snippet(core):
    """Write verilog snippet ('.vs' file) with blocks of this core.
    This snippet may be included manually in verilog modules if needed.
    """
    code = generate_blocks(core)
    out_dir = core.build_dir + "/hardware/src"
    with open(f"{out_dir}/{core.name}_blocks.vs", "w+") as f:
        f.write(code)


def get_instance_port_connections(instance):
    """Returns a multi-line string with all port's signals connections
    for the given Verilog instance.
    """
    instance_portmap = ""
    for port_idx, port in enumerate(instance.ports):
        # If port has 'doc_only' attribute set to True, skip it
        if port.doc_only:
            continue

        assert (
            port.e_connect
        ), f"{iob_colors.FAIL}Port '{port.name}' of instance '{instance.name}' is not connected!{iob_colors.ENDC}"
        newlinechar = "\n"
        assert len(port.signals) == len(
            port.e_connect.signals
        ), f"""{iob_colors.FAIL}Port '{port.name}' of instance '{instance.name}' has different number of signals compared to external connection '{port.e_connect.name}'!
Port '{port.name}' has the following signals:
{newlinechar.join("- " + get_real_signal(port).name for port in port.signals)}

External connection '{get_real_signal(port.e_connect).name}' has the following signals:
{newlinechar.join("- " + get_real_signal(port).name for port in port.e_connect.signals)}
{iob_colors.ENDC}"""

        instance_portmap += f"        // {port.name} port\n"
        # Connect individual signals
        for idx, signal in enumerate(port.signals):
            port_name = signal.name
            real_e_signal = get_real_signal(port.e_connect.signals[idx])
            e_signal_name = real_e_signal.name

            comma = ""
            if port_idx < len(instance.ports) - 1 or idx < len(port.signals) - 1:
                comma = ","

            for bit_slice in port.e_connect_bit_slices:
                if e_signal_name in bit_slice:
                    e_signal_name = bit_slice
                    break

            instance_portmap += f"        .{port_name}({e_signal_name}){comma}\n"

    return instance_portmap
