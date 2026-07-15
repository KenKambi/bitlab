"""Hardware register bit-field mapping, with C code export.

Quick start:
    >>> from bitlab.registers import Register
    >>> reg = Register("UART_CR1", size_bits=8)
    >>> reg.add_field("ENABLE", bit_index=0)
    >>> reg.add_field("MODE", bit_range=(1, 3))
    >>> hex(reg.pack(ENABLE=1, MODE=5))
    '0xb'

Educational trace:
    >>> from bitlab.registers import explain
    >>> print(explain(reg, ENABLE=1, MODE=5))

Export to C:
    >>> from bitlab.registers import export_c
    >>> print(export_c(reg))                    # portable #define/mask macros
    >>> print(export_c(reg, style="struct"))     # C bit-field struct
"""

from .codegen import export_c
from .core import Field, Register
from .explain import explain

__all__ = ["Register", "Field", "explain", "export_c"]
