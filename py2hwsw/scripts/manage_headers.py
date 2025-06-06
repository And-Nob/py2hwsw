#!/usr/bin/python3

# SPDX-FileCopyrightText: 2025 IObundle
#
# SPDX-License-Identifier: MIT

"""
Script to manage file headers (including SPDX license headers).
Can insert, remove, and update headers.
Supports multiple file types.

After running this script with the 'spdx' header template, you can use the `reuse` tool
to check if the project is compliant with REUSE Specification.
Check project compliance: `reuse lint`

Download MIT license file: `reuse download MIT`

By default, the spdx header of this script should match the changes made by the `reuse`
tool with this command:
`reuse annotate --copyright="IObundle" --license="MIT" -r . --skip-unrecognised`

Note that this script supports more file types than the `reuse` tool.
And this script overrides existing headers (does not keep old license headers).
"""

import os
import argparse
from datetime import datetime
from jinja2 import Template

FILE_WITH_IGNORE_INFO = ".ignore_file_headers"

comment_char = {
    ".c": "/*",
    ".cpp": "/*",
    ".h": "/*",
    ".py": "#",
    ".v": "//",
    ".vh": "//",
    ".vs": "//",
    ".vhdl": "--",
    ".sh": "#",
    ".mk": "#",
    "Makefile": "#",
    ".nix": "#",
    ".tex": "%",
    ".cls": "%",
    ".yml": "#",
    ".gitignore": "#",
    ".gitmodules": "#",
    ".md": "<!--",
    ".scala": "//",
    ".dts": "//",
    ".sdc": "#",
    ".lds": "/*",
    ".xdc": "#",
    ".tcl": "#",
    ".clang-format": "#",
    ".dfl": "#",
    ".qsys": "<!--",
    ".ccf": "#",
    ".service": "#",
    "Dockerfile": "#",
}

# File extensions with independent license headers
independent_lic_extensions = [
    ".cff",
    ".gtkw",
    ".drom",
    ".expected",
    ".patch",
    ".txt",
    ".pdf",
    ".json",
    ".png",
    ".jpeg",
    ".odg",
    ".ods",
    ".awl",
    ".lib",
    ".rules",
    ".tmp",
]

# Strings used in multiline comments
# Start; Body; End
multiline_comments = {
    "/*": (" *", " */"),
    "<!--": ("", "-->"),
}

# Jinja2 templates for headers
headers = {
    "spdx": """\
{%- for copyright_line in copyright_lines -%}
{{ copyright_line }}
{% endfor %}
{%- for contributor_line in contributor_lines %}
SPDX-FileContributor: {{ contributor_line }}
{% endfor %}

{%- for expression in spdx_expressions %}
SPDX-License-Identifier: {{ expression }}
{% endfor %}
""",
    # NOTE: Add other header templates here
}

DEBUG = 0
VERBOSE = 0


def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="File Header Comment Manager")

    # Add arguments
    parser.add_argument(
        "--header",
        choices=headers.keys(),
        default="spdx",
        help="The header template to use (default: spdx)",
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Path to search for files (default: .)",
    )
    parser.add_argument(
        "--list-files-only",
        default=False,
        help="List the files that would be modified without modifying them",
    )
    parser.add_argument(
        "--delete-only",
        default=False,
        help="Only delete headers from files",
    )
    parser.add_argument(
        "--verbose",
        default=True,
        help="Enable verbose mode",
    )
    parser.add_argument(
        "--debug",
        default=False,
        help="Enable debug mode",
    )
    parser.add_argument(
        "--ignore-paths",
        nargs="+",
        help="List of paths to ignore",
    )

    # SPDX header template arguments
    parser.add_argument(
        "--license",
        default="MIT",
        help="SPDX license identifier (default: MIT)",
    )
    parser.add_argument(
        "--copyright-holder",
        default="IObundle",
        help="SPDX copyright holder (default: IObundle)",
    )
    parser.add_argument(
        "--no-copyright-year",
        default=False,
        help="Do not include copyright year in header",
    )

    # Parse the arguments
    args = parser.parse_args()
    generate_headers(
        root=args.path,
        ignore_paths=args.ignore_paths,
        copyright_holder=args.copyright_holder,
        license_name=args.license,
        header_template=args.header,
        list_files_only=args.list_files_only,
        delete_only=args.delete_only,
        verbose=args.verbose,
        debug=args.debug,
    )


def generate_headers(
    root=".",
    ignore_paths=[],
    copyright_holder="IObundle",
    license_name="MIT",
    header_template="spdx",
    list_files_only=False,
    delete_only=False,
    verbose=False,
    debug=False,
):
    if debug:
        global DEBUG
        DEBUG = 1

    if verbose:
        global VERBOSE
        VERBOSE = 1

    if not ignore_paths:
        ignore_paths = []

    ignore_paths += ["./LICENSES"]

    ignore_files = []
    # Read FILE_WITH_IGNORE_INFO if it exists
    if os.path.isfile(FILE_WITH_IGNORE_INFO):
        print(f"Found ignore configuration file '{FILE_WITH_IGNORE_INFO}'.")
        with open(FILE_WITH_IGNORE_INFO, "r") as f:
            ignore_files += [
                path.strip()
                for path in f.readlines()
                if path.strip() and not path.startswith("#")
            ]

    # Check if there are any directories in ignore_files
    for file in ignore_files:
        if os.path.isdir(file):
            ignore_paths.append(file)
            ignore_files.remove(file)

    # Files that have SPDX license in header
    files = find_files_with_extensions(
        root,
        comment_char.keys(),
        ignore_paths=ignore_paths,
        ignore_files=ignore_files,
    )

    if list_files_only:
        print("\n".join(files))
        return

    template_context = {
        "copyright_lines": [
            f"SPDX-FileCopyrightText: {datetime.now().year} {copyright_holder}",
        ],
        "contributor_lines": [],
        "spdx_expressions": [license_name],
    }

    header = render_jinja_template(headers[header_template], template_context)

    for file in files:
        modify_file_header(
            file,
            header,
            comment_char=comment_char[
                next(ext for ext in comment_char if file.endswith(ext))
            ],
            delete_only=delete_only,
        )

    # Files with corresponding independent license files
    files = find_files_with_extensions(
        root,
        independent_lic_extensions,
        ignore_paths=ignore_paths,
        ignore_files=ignore_files,
    )

    for file in files:
        write_independent_lic_file(file, header)


def write_independent_lic_file(file, header):
    """Given a file path, write a corresponding independent license file."""
    with open(file + ".license", "w") as f:
        f.writelines(header)


def modify_file_header(filepath, new_header, comment_char="#", delete_only=False):
    """
    Modifies the header of a file, replacing it with a new header.

    :param filepath: The path to the file to modify.
    :param new_header: The new header text to insert.
    :param comment_char: The character that starts each header line (default: "#").
    """
    global DEBUG
    try:
        empty_file = 0
        with open(filepath, "r") as file:
            lines = file.readlines()
            empty_file = not len(lines)

        header_start_index = 0
        insert_blank_line = False
        is_multiline = comment_char in multiline_comments
        if not empty_file:
            # Check if file has shebang line
            if lines[0].startswith("#!") or lines[0].startswith("<?xml"):
                header_start_index = 1
                insert_blank_line = True

            if (
                insert_blank_line
                and not lines[header_start_index].strip()
                and lines[header_start_index + 1].startswith(comment_char)
            ):
                # Remove blank line before header
                lines.pop(header_start_index)

            # Check if file already has a header
            # Multi-line
            if is_multiline and lines[header_start_index].startswith(comment_char):
                body_comment_char = multiline_comments[comment_char][0]
                end_comment_char = multiline_comments[comment_char][1]
                # Remove multiline start
                lines.pop(header_start_index)
                # Remove old header body
                while lines[header_start_index].startswith(
                    body_comment_char
                ) and not lines[header_start_index].startswith(end_comment_char):
                    lines.pop(header_start_index)
                # Remove multiline end
                lines.pop(header_start_index)
                # Remove blank line after header
                lines.pop(header_start_index)
            # Not multi-line
            elif lines[header_start_index].startswith(comment_char):
                # Remove old header
                while len(lines) and lines[header_start_index].startswith(comment_char):
                    lines.pop(header_start_index)
                # Remove blank line after header (if any)
                if len(lines):
                    lines.pop(header_start_index)

        # Create the new header lines
        new_header_lines = []

        if insert_blank_line and not delete_only:
            new_header_lines.append("\n")

        # Multi-line
        if is_multiline and not delete_only:
            body_comment_char = multiline_comments[comment_char][0]
            body_comment_char = f"{body_comment_char} " if body_comment_char else ""
            end_comment_char = multiline_comments[comment_char][1]
            new_header_lines.append(f"{comment_char}\n")
            for line in new_header.splitlines():
                body_line_prefix = body_comment_char
                if not line.strip():
                    body_line_prefix = body_comment_char[:-1]
                new_header_lines.append(f"{body_line_prefix}{line}\n")
            new_header_lines.append(f"{end_comment_char}\n")
            new_header_lines.append("\n")
        # Not multi-line
        elif not delete_only:
            for line in new_header.splitlines():
                if line.strip():
                    new_header_lines.append(f"{comment_char} {line}\n")
                else:
                    new_header_lines.append(f"{comment_char}\n")
            new_header_lines.append("\n")

        # Prepare the new content
        if empty_file:
            new_content = new_header_lines  # New header lines
        else:
            new_content = lines[:header_start_index]  # Lines before the header
            new_content += new_header_lines  # New header lines
            new_content += lines[header_start_index:]  # Lines after the old header

        if DEBUG:
            print("".join(new_content))
            return

        # Write the new content back to the file
        with open(filepath, "w") as file:
            file.writelines(new_content)

        if VERBOSE:
            print(f"Header modified successfully in {filepath}")

    except Exception as e:
        print(f"An error occurred for {filepath}: {e}")
        raise (e)


def find_files_with_extensions(directory, extensions, ignore_paths=[], ignore_files=[]):
    """
    Search for files with specified extensions in a directory recursively.

    :param directory: The root directory to start the search.
    :param extensions: A list of file extensions to search for.
    :return: A list of file paths that match the specified extensions.
    """
    matching_files = []

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        # Ignore specified paths
        if root in ignore_paths:
            dirs[:] = []
            if VERBOSE:
                print(f"Ignoring path {root}")
            continue
        for file in files:
            # Ignore specified files
            if root + "/" + file in ignore_files:
                if VERBOSE:
                    print(f"Ignoring file {root + '/' + file}")
                continue
            # Check if the file has one of the specified extensions
            if any(file.endswith(ext) for ext in extensions):
                # Construct the full file path and add it to the list
                matching_files.append(os.path.join(root, file))

    return matching_files


def render_jinja_template(template_string, context):
    """
    Renders a Jinja2 template from a multiline string with the given context.

    :param template_string: The Jinja2 template as a multiline string.
    :param context: A dictionary containing the context variables for the template.
    :return: The rendered template as a string.
    """
    # Create a Jinja2 Template object from the template string
    template = Template(template_string)

    # Render the template with the provided context
    rendered_output = template.render(context)

    return rendered_output


if __name__ == "__main__":
    main()
