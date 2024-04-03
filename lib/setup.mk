# (c) 2022-Present IObundle, Lda, all rights reserved
#
# This file is run as a makefile to setup a build directory for an IP core
#

CORE_DIR ?=.

setup-python-dir:
ifeq ($(IOB_PYTHONPATH),)
	$(error "IOB_PYTHONPATH is not set")
endif
	mkdir -p $(IOB_PYTHONPATH)
	find . -name \*.py -exec cp -u {} $(IOB_PYTHONPATH) \;

build-setup: setup-python-dir format-all
	python3 -B $(CORE_DIR)/$(CORE).py $(SETUP_ARGS)

python-lint:
	$(LIB_DIR)/scripts/sw_tools.py mypy .

python-format:
	$(LIB_DIR)/scripts/sw_tools.py black . 
ifneq ($(wildcard $(BUILD_DIR)),)
	$(LIB_DIR)/scripts/sw_tools.py black $(BUILD_DIR) 
endif

c-format:
	$(LIB_DIR)/scripts/sw_tools.py clang .
ifneq ($(wildcard $(BUILD_DIR)),)
	$(LIB_DIR)/scripts/sw_tools.py clang $(BUILD_DIR)
endif

# Auto-disable linter and formatter if setting up with the Tester
ifeq ($(TESTER),1)
	DISABLE_LINT:=1
	DISABLE_FORMAT:=1
endif

# Verilog files in build directory
verilog_files:
	$(eval VHFILES = $(shell find $(BUILD_DIR)/hardware -type f -name "*.vh" -not -path "*version.vh" -not -path "*test_*.vh"))
	$(eval VFILES = $(shell find $(BUILD_DIR)/hardware -type f -name "*.v"))

# Run linter on all verilog files
verilog-lint: verilog_files
ifneq ($(DISABLE_LINT),1)
	$(LIB_DIR)/scripts/verilog-lint.py $(VHFILES) $(VFILES)
endif

# Run formatter on all verilog files
verilog-format: verilog-lint
ifneq ($(DISABLE_FORMAT),1)
	$(LIB_DIR)/scripts/verilog-format.sh $(VHFILES) $(VFILES)
endif

format-all: python-format c-format verilog-lint verilog-format # python-lint 

clean: setup-python-dir
#ifneq ($(wildcard $(BUILD_DIR)),)
	python3 -B $(CORE_DIR)/$(CORE).py clean
#endif
	# Makefile only runs the 'setup-python-dir' target once: https://stackoverflow.com/a/38212629
	# So if we delete it here, it wont be rebuilt on 'build-setup'
	#@rm -rf $(IOB_PYTHONPATH)
	@rm -rf ../*.summary ../*.rpt 
	@find . -name \*~ -delete

# Remove all __pycache__ folders with python bytecode
python-cache-clean:
	find . -name "*__pycache__" -exec rm -rf {} \; -prune


.PHONY: setup-python-dir build-setup clean c-format python-lint python-format verilog-format format-all
