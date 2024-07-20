from dataclasses import dataclass
from typing import Dict

import iob_colors
import if_gen
from iob_wire import iob_wire
from iob_base import convert_dict2obj_list, fail_with_msg
from iob_signal import iob_signal


@dataclass
class iob_port(iob_wire):
    """Describes an IO port."""

    # External wire that connects this port
    e_connect: iob_wire | None = None
    doc_only: bool = False

    def __post_init__(self):
        if not self.name:
            fail_with_msg("Port name is not set", ValueError)

        if self.interface:
            self.signals += if_gen.get_signals(
                self.interface.type,
                self.interface.subtype,
                self.interface.mult,
                self.interface.widths,
            )

        for signal in self.signals:
            if not signal.direction:
                raise Exception("Port direction is required")
            elif signal.direction not in ["input", "output", "inout"]:
                raise Exception(
                    "Error: Direction must be 'input', 'output', or 'inout'."
                )

    def connect_external(self, wire):
        """Connects the port to an external wire"""
        self.e_connect = wire


def create_port(core, *args, signals=[], interface=None, **kwargs):
    """Creates a new port object and adds it to the core's port list
    Also creates a new internal module wire to connect to the new port
    param core: core object
    """
    # Ensure 'ports' list exists
    core.set_default_attribute("ports", [])
    # Convert user signal dictionaries into 'iob_signal' objects
    sig_obj_list = convert_dict2obj_list(signals, iob_signal)
    # Convert user interface dictionary into 'if_gen.interface' object
    interface_obj = if_gen.dict2interface(interface) if interface else None
    port = iob_port(*args, signals=sig_obj_list, interface=interface_obj, **kwargs)
    core.ports.append(port)


def get_signal_name_with_dir_suffix(signal: Dict):
    """Returns a signal name with the direction suffix appended
    param signal: signal dictionary
    """
    if signal.direction == "input":
        return f"{signal.name}_i"
    elif signal.direction == "output":
        return f"{signal.name}_o"
    elif signal.direction == "inout":
        return f"{signal.name}_io"
    raise Exception(
        f"{iob_colors.FAIL}Unknown direction '{signal.direction}'"
        f" in '{signal.name}'!{iob_colors.ENDC}"
    )
