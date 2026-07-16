"""Computer architecture toolkit: IEEE 754 float deconstruction, endianness
conversion, Gray code, and Q-format fixed-point conversion.

Quick start:
    >>> from bitlab.arch import decompose
    >>> decompose(0.15625).classification
    'normal'

    >>> from bitlab.arch import swap_endianness
    >>> hex(swap_endianness(0x12345678, 4))
    '0x78563412'

    >>> from bitlab.arch import binary_to_gray, gray_to_binary
    >>> binary_to_gray(0b1011)
    14

    >>> from bitlab.arch import float_to_q, q_to_float
    >>> float_to_q(0.5, "Q1.15")
    16384

Educational traces:
    >>> from bitlab.arch import explain_float, explain_endianness, explain_gray, explain_fixed_point

C export (endianness + fixed-point only -- see codegen module docstring):
    >>> from bitlab.arch import export_c_endian_swap, export_c_fixed_point
"""

from .codegen import export_c_endian_swap, export_c_fixed_point
from .endianness import (
    from_bytes,
    swap_endianness,
    to_big_endian,
    to_bytes,
    to_little_endian,
)
from .explain import explain_endianness, explain_fixed_point, explain_gray, explain_float
from .fixed_point import float_to_q, parse_q_format, q_range, q_to_float
from .gray import binary_to_gray, gray_to_binary
from .ieee754 import IEEE754Components, compose, decompose, from_bits, to_bits

__all__ = [
    # ieee754
    "decompose",
    "compose",
    "to_bits",
    "from_bits",
    "IEEE754Components",
    "explain_float",
    # endianness
    "swap_endianness",
    "to_bytes",
    "from_bytes",
    "to_big_endian",
    "to_little_endian",
    "explain_endianness",
    "export_c_endian_swap",
    # gray code
    "binary_to_gray",
    "gray_to_binary",
    "explain_gray",
    # fixed point
    "float_to_q",
    "q_to_float",
    "q_range",
    "parse_q_format",
    "explain_fixed_point",
    "export_c_fixed_point",
]
