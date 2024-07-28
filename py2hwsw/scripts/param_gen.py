#!/usr/bin/env python3


def has_params(confs):
    """Check if given 'confs' list has any parameters"""
    for conf in confs:
        if conf.type in ["P", "F"]:
            return True
    return False


def generate_params(core):
    module_parameters = [p for p in core.confs if p.type in ["P", "F"]]
    out_dir = core.build_dir + "/hardware/src"

    if not has_params(core.confs):
        return

    # Generate params.vs
    lines = []
    core_prefix = f"{core.name}_".upper()
    for parameter in module_parameters:
        p_name = parameter.name.upper()
        lines.append(f"    parameter {p_name} = `{core_prefix}{p_name},\n")
    lines[-1] = lines[-1].replace(",\n", "\n")
    file2create = open(f"{out_dir}/{core.name}_params.vs", "w")
    file2create.writelines(lines)
    file2create.close()

    generate_inst_params(core)


def generate_inst_params(core):
    # Generate inst_params.vs
    instance_parameters = core.parameters
    out_dir = core.build_dir + "/hardware/src"
    lines = []
    for p_name, p_value in instance_parameters.items():
        lines.append(f"        .{p_name}({p_value}),\n")
    if lines:
        lines[-1] = lines[-1].replace(",\n", "\n")
    file2create = open(f"{out_dir}/{core.instance_name}_{id(core)}_inst_params.vs", "w")
    file2create.writelines(lines)
    file2create.close()
