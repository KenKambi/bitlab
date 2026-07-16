"""IEEE 754 floating-point deconstruction.

Decomposes a Python float into its raw sign/exponent/mantissa bit fields (or
reassembles one from those fields), for 32-bit (single) and 64-bit (double)
precision.

The conversion goes through Python's `struct` module rather than
reimplementing floating-point encoding by hand -- `struct` IS the platform's
native IEEE 754 implementation, so this can't drift from correct behavior on
special values (zero, subnormals, infinities, NaN) the way a hand-rolled
bit-twiddling implementation easily could.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

_SPECS = {
    # width: (exponent_bits, mantissa_bits, bias, struct_float_code, struct_int_code)
    32: (8, 23, 127, "f", "I"),
    64: (11, 52, 1023, "d", "Q"),
}


def _spec(width: int):
    if width not in _SPECS:
        raise ValueError(f"width must be 32 or 64 (got {width})")
    return _SPECS[width]


def to_bits(value: float, width: int = 32) -> int:
    """Returns the raw IEEE 754 bit pattern of `value` as an unsigned integer."""
    _, _, _, float_code, int_code = _spec(width)
    packed = struct.pack(f">{float_code}", value)
    return struct.unpack(f">{int_code}", packed)[0]


def from_bits(bits: int, width: int = 32) -> float:
    """Reassembles a float from a raw IEEE 754 bit pattern."""
    _, _, _, float_code, int_code = _spec(width)
    packed = struct.pack(f">{int_code}", bits)
    return struct.unpack(f">{float_code}", packed)[0]


@dataclass(frozen=True)
class IEEE754Components:
    """The decomposed pieces of an IEEE 754 float."""

    width: int
    value: float
    bits: int
    sign: int
    """0 (positive) or 1 (negative)."""
    exponent_raw: int
    """The biased exponent field exactly as stored."""
    exponent: int
    """The unbiased (true) exponent."""
    mantissa: int
    """The raw mantissa/fraction bits (the part after the implicit leading 1)."""
    classification: str
    """One of: 'zero', 'subnormal', 'normal', 'infinity', 'nan'."""


def decompose(value: float, width: int = 32) -> IEEE754Components:
    """Breaks `value` down into its IEEE 754 sign/exponent/mantissa fields."""
    exp_bits, mantissa_bits, bias, _, _ = _spec(width)
    bits = to_bits(value, width)

    sign = (bits >> (width - 1)) & 1
    exponent_raw = (bits >> mantissa_bits) & ((1 << exp_bits) - 1)
    mantissa = bits & ((1 << mantissa_bits) - 1)
    exp_all_ones = (1 << exp_bits) - 1

    if exponent_raw == 0 and mantissa == 0:
        classification = "zero"
        exponent = 0
    elif exponent_raw == 0:
        classification = "subnormal"
        exponent = 1 - bias
    elif exponent_raw == exp_all_ones:
        classification = "nan" if mantissa != 0 else "infinity"
        exponent = exponent_raw - bias
    else:
        classification = "normal"
        exponent = exponent_raw - bias

    return IEEE754Components(
        width=width,
        value=value,
        bits=bits,
        sign=sign,
        exponent_raw=exponent_raw,
        exponent=exponent,
        mantissa=mantissa,
        classification=classification,
    )


def compose(sign: int, exponent_raw: int, mantissa: int, width: int = 32) -> float:
    """Reassembles a float from raw sign/biased-exponent/mantissa fields
    (the inverse of `decompose`, working from the raw stored fields rather
    than the unbiased exponent)."""
    exp_bits, mantissa_bits, _, _, _ = _spec(width)

    if sign not in (0, 1):
        raise ValueError("sign must be 0 or 1")
    if not (0 <= exponent_raw < (1 << exp_bits)):
        raise ValueError(f"exponent_raw must fit in {exp_bits} bits")
    if not (0 <= mantissa < (1 << mantissa_bits)):
        raise ValueError(f"mantissa must fit in {mantissa_bits} bits")

    bits = (sign << (width - 1)) | (exponent_raw << mantissa_bits) | mantissa
    return from_bits(bits, width)
