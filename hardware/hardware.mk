ifeq ($(filter REGFILEIF, $(HW_MODULES)),)

include $(REGFILEIF_DIR)/config.mk

#add itself to HW_MODULES list
HW_MODULES+=REGFILEIF


REGFILEIF_INC_DIR:=$(REGFILEIF_HW_DIR)/include
REGFILEIF_SRC_DIR:=$(REGFILEIF_HW_DIR)/src

USE_NETLIST ?=0

#include files
VHDR+=$(wildcard $(REGFILEIF_INC_DIR)/*.vh)
VHDR+=iob_regfileif_swreg_gen.vh iob_regfileif_swreg_def.vh
VHDR+=$(LIB_DIR)/hardware/include/iob_lib.vh

#hardware include dirs
INCLUDE+=$(incdir). $(incdir)$(REGFILEIF_INC_DIR) $(incdir)$(LIB_DIR)/hardware/include

#sources
VSRC+=$(REGFILEIF_SRC_DIR)/iob_regfileif.v

regfileif-hw-clean: regfileif-gen-clean
	@rm -f *.v *.vh

.PHONY: regfileif-hw-clean

endif
