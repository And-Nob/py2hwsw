#!/usr/bin/env python3

import os
import shutil
import copy

import iob_colors
from iob_module import iob_module
from mkregs import mkregs

# Submodules
from iob_reg import iob_reg
from iob_reg_e import iob_reg_e


class iob_regfileif(iob_module):
    name = 'iob_regfileif'
    version = "V0.10"
    flows = ""
    setup_dir = os.path.dirname(__file__)

    @classmethod
    def _create_submodules_list(cls):
        ''' Create submodules list with dependencies of this module
        '''
        super()._create_submodules_list([
            {"interface": "iob_s_port"},
            {"interface": "iob_s_portmap"},
            iob_reg,
            iob_reg_e,
        ])

    @classmethod
    def _specific_setup(cls):
        # Hardware headers & modules
        # Verilog modules instances
        # TODO

        # Ensure user has configured registers for this peripheral
        assert cls.regs, f"{iob_colors.FAIL}REGFILEIF register list is empty.{iob_colors.ENDC}"

    @classmethod
    def _generate_files(cls):
        super()._generate_files()

        #### Invert registers type to create drivers for Secondary system
        inverted_regs = copy.deepcopy(cls.regs)
        for table in inverted_regs: 
            for reg in table['regs']:
                # Don't invert VERSION register
                if reg['name'] == 'VERSION':
                    continue
                # Invert register type
                if reg['type'] == 'W': reg['type']='R'
                else: reg['type']='W'

        #### Create an instance of the mkregs class inside the mkregs module
        mkregs_obj = mkregs()
        mkregs_obj.config = cls.confs
        # Get register table
        reg_table = mkregs_obj.get_reg_table(inverted_regs, False)
        # Create inverted register hardware
        mkregs_obj.write_hwheader(reg_table, cls.build_dir+'/hardware/src', f"{cls.name}_inverted")
        mkregs_obj.write_hwcode(reg_table, cls.build_dir+'/hardware/src', f"{cls.name}_inverted")

        #### Modify `*_swreg_inst.vs` file to prevent overriding definitions of the `*_inverted_swreg_inst.vs` file
        with open(f"{cls.build_dir}/hardware/src/{cls.name}_swreg_inst.vs", "r") as file:
            lines = file.readlines()
        # Modify lines
        for idx, line in enumerate(lines):
            # Remove wires, as they have already been declared in the `*_inverted_swreg_inst.vs` file
            if line.startswith("wire "): lines[idx] = ""
            # Replace name of swreg_0 instance
            if line.startswith(") swreg_0 ("): lines[idx] = ") swreg_1 (\n"
            # Rename `iob_ready_ and iob_rvalid` ports as this mapping was already used in the `*_inverted_swreg_inst.vs` file
            if '.iob_ready_nxt_o' in line: lines[idx] = ".iob_ready_nxt_o(iob_ready_nxt2),\n"
            if '.iob_rvalid_nxt_o' in line: lines[idx] = ".iob_rvalid_nxt_o(iob_rvalid_nxt2),\n"
            # Remove `iob_s_portmap.vs` as this mapping was already used in the `*_inverted_swreg_inst.vs` file
            if '`include "iob_s_s_portmap.vs"' in line:
                lines[idx] = ""
                #Insert correct portmap. The normal (non inverted) registers are connected to the external interface that connects to the primary system.
                lines.insert(idx,".iob_avalid_i(external_iob_avalid_i), //Request valid.\n")
                lines.insert(idx,".iob_addr_i(external_iob_addr_i), //Address.\n")
                lines.insert(idx,".iob_wdata_i(external_iob_wdata_i), //Write data.\n")
                lines.insert(idx,".iob_wstrb_i(external_iob_wstrb_i), //Write strobe.\n")
                lines.insert(idx,".iob_rvalid_o(external_iob_rvalid_o), //Read data valid.\n")
                lines.insert(idx,".iob_rdata_o(external_iob_rdata_o), //Read data.\n")
                lines.insert(idx,".iob_ready_o(external_iob_ready_o), //Interface ready.\n")
            # Replace "_r" and "_w" suffixes of registers
            if "_r)" in line:
                lines[idx] = lines[idx].replace("_r)", "_w)")
            else:
                lines[idx] = lines[idx].replace("_w)", "_r)")
        # Insert 2 wires for iob_ready_nxt and iob_rvalid_nxt ports
        lines.insert(0,"wire iob_ready_nxt2;\n")
        lines.insert(0,"wire iob_rvalid_nxt2;\n")
        # Write modified lines to file
        with open(f"{cls.build_dir}/hardware/src/{cls.name}_swreg_inst.vs", "w") as file:
            file.writelines(lines)

        #### Modify "iob_regfileif_inverted_swreg_def" to include `IOB_REGFILEIF_SWREG_ADDR_W`
        with open(f"{cls.build_dir}/hardware/src/{cls.name}_inverted_swreg_def.vh", "r") as file: lines = file.readlines()
        for idx, line in enumerate(lines):
            if line.startswith("`define IOB_REGFILEIF_INVERTED_SWREG_ADDR_W"):
                lines.insert(idx,line.replace("_INVERTED",""))
                break
        with open(f"{cls.build_dir}/hardware/src/{cls.name}_inverted_swreg_def.vh", "w") as file: file.writelines(lines)

        #### Create params, inst_params and conf files for inverted hardware. (Use symlinks to save disk space and highlight they are equal)
        if not os.path.isfile(f"{cls.build_dir}/hardware/src/{cls.name}_inverted_conf.vh"): os.symlink(f"{cls.name}_conf.vh", f"{cls.build_dir}/hardware/src/{cls.name}_inverted_conf.vh")
        if not os.path.isfile(f"{cls.build_dir}/hardware/src/{cls.name}_inverted_params.vs"): shutil.copy(f"{cls.build_dir}/hardware/src/{cls.name}_params.vs", f"{cls.build_dir}/hardware/src/{cls.name}_inverted_params.vs")
        if not os.path.isfile(f"{cls.build_dir}/hardware/src/{cls.name}_inverted_inst_params.vs"): shutil.copy(f"{cls.build_dir}/hardware/src/{cls.name}_inst_params.vs", f"{cls.build_dir}/hardware/src/{cls.name}_inverted_inst_params.vs")

        #### Create inverted register software
        mkregs_obj.write_swheader(reg_table, cls.build_dir+'/software/src', f"{cls.name}_inverted")
        mkregs_obj.write_swcode(reg_table, cls.build_dir+'/software/src', f"{cls.name}_inverted")

        #### Create pc-emul drivers
        # Copy iob_regfileif_inverted_swreg_emb.c
        shutil.copyfile(f"{cls.build_dir}/software/src/{cls.name}_inverted_swreg_emb.c",
                        f"{cls.build_dir}/software/src/{cls.name}_inverted_swreg_pc_emul.c")

        # Modify copied iob_regfileif_inverted_swreg_pc_emul.c file
        with open(f"{cls.build_dir}/software/src/{cls.name}_inverted_swreg_pc_emul.c", "r") as file: 
            contents = file.readlines()
        for idx, line in enumerate(contents):
            # Always return '1' on read registers
            if 'return' in line: contents[idx] = 'return 1; //Always return "1"\n'
            # Do nothing in write registers
            if 'value));' in line: contents[idx] = '//Not implemented \n'
        with open(f"{cls.build_dir}/software/src/{cls.name}_inverted_swreg_pc_emul.c", "w") as file: 
            file.writelines(contents)


    @classmethod
    def _setup_confs(cls):
        super()._setup_confs([
            # Macros

            # Parameters
            {'name':'DATA_W',          'type':'P', 'val':'32', 'min':'NA', 'max':'32', 'descr':"Data bus width"},
            {'name':'ADDR_W',          'type':'P', 'val':'`IOB_REGFILEIF_SWREG_ADDR_W', 'min':'NA', 'max':'32', 'descr':"Address bus width"},
            {'name':'EXTERNAL_DATA_W', 'type':'P', 'val':'32', 'min':'NA', 'max':'32', 'descr':"External data bus width"},
            {'name':'EXTERNAL_ADDR_W', 'type':'P', 'val':'`IOB_REGFILEIF_SWREG_ADDR_W', 'min':'NA', 'max':'32', 'descr':"External address bus width"},
        ])

    @classmethod
    def _setup_ios(cls):
        cls.ios += [
            {'name': 'iob_s_port', 'descr':'CPU native interface', 'ports': [
            ]},
            {'name': 'external_iob_s_port', 'descr':'External CPU native interface', 'ports': [
            ]},
            {'name': 'general', 'descr':'General interface signals', 'ports': [
                {'name':"clk_i" , 'type':"I", 'n_bits':'1', 'descr':"System clock input"},
                {'name':"arst_i", 'type':"I", 'n_bits':'1', 'descr':"System reset, asynchronous and active high"},
                {'name':"cke_i", 'type':"I", 'n_bits':'1', 'descr':"System clock enable signal."},
            ]},
        ]
