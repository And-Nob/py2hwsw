interrupt_csrs = [
    {
        "name": "status",
        "type": "R",
        "n_bits": 32,
        "rst_val": 0,
        "log2n_items": 0,
        "autoreg": True,
        "descr": "Interrupts status: active (1), inactive (0).",
    },
    {
        "name": "mask",
        "type": "W",
        "n_bits": 32,
        "rst_val": 0,
        "log2n_items": 0,
        "autoreg": True,
        "descr": "Interrupts mask: enable (0), disable (1) for each interrupt.",
    },
    {
        "name": "clear",
        "type": "W",
        "n_bits": 32,
        "rst_val": 0,
        "log2n_items": 0,
        "autoreg": True,
        "descr": "Interrupts clear: clear (1), do not clear (0) for each interrupt.",
    },
]


def find_and_update_interrupt_csrs(csrs_dict):
    """Given a dictionary of CSRs, find the interrupt CSRs group and update the dictionary
    accordingly.
    User should provide a CSR of type "INTERRUPT". This CSR will be replaced by interrupt_csrs.
    """
    csr_group_ref = None
    csr_ref = None
    for csr_group in csrs_dict:
        for csr in csr_group["regs"]:
            if csr["type"] == "INTERRUPT":
                csr_group_ref = csr_group
                csr_ref = csr
                break
        if csr_ref:
            break

    if not csr_ref:
        return

    # Add interrupt_csrs to group
    csr_group_ref["regs"] += interrupt_csrs

    # Remove original csr from csr_group
    csr_group_ref["regs"].pop(csr_ref)
