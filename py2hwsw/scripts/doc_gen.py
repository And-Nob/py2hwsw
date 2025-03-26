# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT

#
#    doc_gen.py: generate documentation
#
import os

import config_gen
import io_gen
import block_gen

from latex import write_table
from iob_base import fail_with_msg, find_file


def generate_docs(core):
    """Generate common documentation files"""
    if core.is_top_module:
        config_gen.generate_confs_tex(core.confs, core.build_dir + "/document/tsrc")
        io_gen.generate_ios_tex(core.ports, core.build_dir + "/document/tsrc")
        block_gen.generate_subblocks_tex(
            core.subblocks, core.build_dir + "/document/tsrc"
        )
        generate_py_params_tex(
            core.python_parameters, core.build_dir + "/document/tsrc"
        )


def generate_tex_py2hwsw_attributes(iob_core_instance, out_dir):
    """Generate TeX table of supported attributes of the py2hwsw interface.
    The attributes listed can be used in the 'attributes' dictionary of cores.
    :param iob_core_instance: Dummy instance of the iob_core class. Used to obtain attributes of iob_core.
    :param out_dir: Path to the output directory
    """

    tex_table = []
    for name in iob_core_instance.ATTRIBUTE_PROPERTIES.keys():
        tex_table.append(
            [
                name,
                iob_core_instance.ATTRIBUTE_PROPERTIES[name].datatype,
                iob_core_instance.ATTRIBUTE_PROPERTIES[name].descr,
            ]
        )

    write_table(f"{out_dir}/py2hwsw_attributes", tex_table)


def generate_tex_py2hwsw_standard_py_params(out_dir):
    """Generate TeX table of standard Python Parameters given by py2hwsw to every core.
    The Python Parameters listed are always received in the argument of the core's setup() function.
    :param iob_core_instance: Dummy instance of the iob_core class. Used to obtain python parameters of iob_core.
    :param out_dir: Path to the output directory
    """

    tex_table = [
        [
            "core_name",
            str,
            "Name of current core (determined by the core's file name).",
        ],
        [
            "build_dir",
            str,
            "Build directory of this core. Usually defined by `--build-dir` flag or instantiator.",
        ],
        [
            "py2hwsw_target",
            str,
            "The reason why py2hwsw is invoked. Usually `setup` meaning the Py2HWSW is calling the core's script to obtain information on how to generate the core. May also be other targets like `clean`, `print_attributes`, or `deliver`. These are usually to obtain information about the core for various purposes, but not to generate the build directory.",
        ],
        [
            "instantiator",
            dict,
            "Core dictionary with attributes of the instantiator core (if any). Allows subblocks to obtain information about their instantiator core.",
        ],
        [
            "py2hwsw_version",
            str,
            "Version of Py2HWSW.",
        ],
    ]

    write_table(f"{out_dir}/py2hwsw_py_params", tex_table)


def generate_tex_core_lib(out_dir):
    """Generate TeX table of cores available in py2hwsw library.
    :param out_dir: Path to the output directory
    """
    lib_path = os.path.join(os.path.dirname(__file__), "../lib")

    tex_table = []
    # Find all .py files under lib_path
    for root, dirs, files in os.walk(lib_path):
        # Skip specific directories
        if os.path.basename(root) in ["scripts", "test", "document"]:
            dirs[:] = []
            continue
        for file in files:
            if file.endswith(".py"):
                tex_table.append(
                    [
                        os.path.splitext(file)[0],
                        os.path.relpath(root, lib_path),
                    ]
                )

    write_table(f"{out_dir}/py2hwsw_core_lib", tex_table)


def generate_py_params_tex(python_parameters, out_dir):
    """Generate TeX section for python parameters of given core.
    :param list python_parameters: list of python parameter groups
    :param str out_dir: path to output directory
    """

    py_params_file = open(f"{out_dir}/py_params.tex", "w")

    # FIXME: These python parameters are only used during the setup process. So from the point of view of the build directory, they are not needed.
    # Maybe we should have a user guide specific for the setup stage?
    py_params_file.write(
        """
The following tables describe the supported \\textit{Python Parameters} for the setup of this IP core.
Note that these \\textit{Python Parameters} are not used during the build process of this core from this build directory.
They only serve a purpose during the setup process, to configure how the core build directory will be generated.
See the \\textit{Python Parameters} section of the \\href{https://github.com/IObundle/py2hwsw/blob/main/py2hwsw/py2hwsw_document/document/ug.pdf}{Py2HWSW User Guide} for more details.
"""
    )

    for group in python_parameters:
        py_params_file.write(
            """
\\begin{table}[H]
  \\centering
  \\begin{tabularx}{\\textwidth}{|l|c|X|}

    \\hline
    \\rowcolor{iob-green}
    {\\bf Name} & {\\bf Default Value} & {\\bf Description} \\\\ \\hline \\hline

    \\input """
            + group.name
            + """_py_params_tab

  \\end{tabularx}
  \\caption{"""
            + group.descr.replace("_", "\\_")
            + """}
  \\label{"""
            + group.name
            + """_py_params_tab:is}
\\end{table}
"""
        )
        if group.doc_clearpage:
            py_params_file.write("\\clearpage")

    py_params_file.write("\\clearpage")
    py_params_file.close()

    generate_py_params_tex_table(python_parameters, out_dir)


def generate_py_params_tex_table(python_parameters, out_dir):
    """Create TeX table for each python parameter group in given list.
    :param list python_parameters: list of python parameter groups
    :param str out_dir: path to output directory
    """

    for group in python_parameters:
        tex_table = []
        for param in group.python_parameters:
            tex_table.append(
                [
                    param.name,
                    param.val,
                    param.descr,
                ]
            )

        # Write table with true parameters and macros
        write_table(f"{out_dir}/{group.name}_py_params", tex_table)


def process_tex_macros(tex_src_dir):
    """Search for special macros in TeX sources and replace them with appropriate values.
    :param tex_src_dir: Path to directory with TeX sources to be processed
    """
    tex_files = [f for f in os.listdir(tex_src_dir) if f.endswith(".tex")]

    for file in tex_files:
        with open("file.txt", "r") as file:
            lines = file.readlines()

        for idx, line in enumerate(lines):
            if line.strip().startswith("% py2_macro:"):
                lines[idx] = process_tex_macro(line)

        with open("file.txt", "w") as file:
            file.writelines(lines)


def process_tex_macro(line):
    """Given a TeX macro line, return a new (multi)line with appropriate value."""
    macro = line.strip().split(":")[1].strip().split()
    macro_command = macro[0]
    listing_content = ""

    def _find_file(file):
        """Local function to find file, and print error otherwise"""
        filename, extension = file.split(".")
        file = find_file(
            os.pwath.join(os.path.dirname(__file__), ".."),
            filename,
            filter_extensions=[extension],
        )
        if not file:
            fail_with_msg(f"File '{filename}' not found! From macro line '{line}'.")
        return file

    if macro_command == "listing":
        # Search for given attribute/class/method, and print its body
        code_obj_name = macro[1]
        file = _find_file(macro[macro.index("from") + 1])
        with open(file, "r") as f:
            # Search for start line and print lines after it
            _lines = f.readlines()
            for _line in _lines:
                if _line.strip().startswith("def " + code_obj_name):
                    # Copy method body
                    # TODO:
                    break
                elif _line.strip().startswith(code_obj_name):
                    # Copy attribute body
                    # TODO:
                    break
                elif _line.strip().startswith("class " + code_obj_name):
                    # Copy class body
                    # TODO:
                    break
    elif macro_command == "class_attributes":
        # Search for given class, and print only its attributes (not methods)
        class_name = macro[1]
        file = _find_file(macro[macro.index("from") + 1])
        # Copy class attributes
        # TODO:
    elif macro_command == "file":
        # Replace with content of given file
        file = _find_file(macro[1])
        # Copy file contents
        with open(file, "r") as f:
            listing_content = f.read()
    elif macro_command == "start_line":
        # Search for start line and print lines after it
        start_line = macro[1]
        file = _find_file(macro[macro.index("from") + 1])
        end_line = None
        if "end_line" in macro:
            end_line = macro[macro.index("end_line") + 1]
        # Find start line
        # Copy lines until end line
        # TODO:
    else:
        fail_with_msg(f"Unknown macro command '{macro_command}' in line '{line}'!")

    return """
\\begin{tiny}
  \\begin{lstlisting}
{listing_content}
  \\end{lstlisting}
\\end{tiny}
"""
