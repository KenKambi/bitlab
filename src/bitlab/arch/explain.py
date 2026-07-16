"""Human-readable, step-by-step explanations for each `bitlab.arch` topic —
the educational counterpart to the compute functions in `ieee754.py`,
`endianness.py`, `gray.py`, and `fixed_point.py`.
"""

from __future__ import annotations

from .endianness import swap_endianness
from .fixed_point import parse_q_format
from .gray import binary_to_gray
from .ieee754 import decompose


def explain_float(value: float, width: int = 32) -> str:
    """Step-by-step breakdown of how `value` is stored as an IEEE 754 float."""
    c = decompose(value, width)
    exp_bits = {32: 8, 64: 11}[width]
    mantissa_bits = {32: 23, 64: 52}[width]
    bias = {32: 127, 64: 1023}[width]

    lines = []
    lines.append(f"IEEE 754 {'single' if width == 32 else 'double'}-precision ({width}-bit)")
    lines.append(f"Value: {value}")
    lines.append("")
    lines.append(f"Raw bits: {c.bits:0{width}b}")
    lines.append(
        f"          {'S' * 1}{'E' * exp_bits}{'M' * mantissa_bits}"
        f"  (S=sign, E=exponent, M=mantissa)"
    )
    lines.append("")
    lines.append(f"Sign bit:      {c.sign}  ({'negative' if c.sign else 'positive'})")
    lines.append(
        f"Exponent bits: {c.exponent_raw:0{exp_bits}b} = {c.exponent_raw} (raw, biased by {bias})"
    )
    lines.append(f"Mantissa bits: {c.mantissa:0{mantissa_bits}b} = {c.mantissa} (raw fraction)")
    lines.append("")
    lines.append(f"Classification: {c.classification}")

    if c.classification == "normal":
        lines.append(f"Unbiased exponent: {c.exponent_raw} - {bias} = {c.exponent}")
        mantissa_fraction = c.mantissa / (1 << mantissa_bits)
        lines.append(
            f"Implied leading 1: value = (-1)^{c.sign} x (1 + {c.mantissa}/2^{mantissa_bits}) x 2^{c.exponent}"
        )
        lines.append(f"                 = (-1)^{c.sign} x {1 + mantissa_fraction} x 2^{c.exponent}")
        lines.append(f"                 = {value}")
    elif c.classification == "subnormal":
        lines.append(
            f"Subnormal: no implied leading 1. "
            f"value = (-1)^{c.sign} x ({c.mantissa}/2^{mantissa_bits}) x 2^{c.exponent}"
        )
    elif c.classification == "zero":
        lines.append(f"Zero (all exponent and mantissa bits are 0): {'-0.0' if c.sign else '0.0'}")
    elif c.classification == "infinity":
        lines.append(f"Infinity: {'-inf' if c.sign else '+inf'} (all-1 exponent, zero mantissa)")
    elif c.classification == "nan":
        lines.append("NaN: all-1 exponent, non-zero mantissa")

    return "\n".join(lines)


def explain_endianness(value: int, width_bytes: int) -> str:
    """Byte-by-byte trace of swapping `value`'s byte order."""
    original_bytes = value.to_bytes(width_bytes, byteorder="big")
    swapped = swap_endianness(value, width_bytes)
    swapped_bytes = swapped.to_bytes(width_bytes, byteorder="big")

    lines = []
    lines.append(f"Value: 0x{value:0{width_bytes * 2}X} ({width_bytes} bytes)")
    lines.append(f"Big-endian byte order:    {' '.join(f'{b:02X}' for b in original_bytes)}")
    lines.append(f"Little-endian byte order: {' '.join(f'{b:02X}' for b in original_bytes[::-1])}")
    lines.append("")
    lines.append("Swapping byte order (reversing byte sequence):")
    for i, b in enumerate(original_bytes):
        lines.append(f"  byte[{i}] = 0x{b:02X}  ->  new position {width_bytes - 1 - i}")
    lines.append("")
    lines.append(f"Result: 0x{swapped:0{width_bytes * 2}X}")
    return "\n".join(lines)


def explain_gray(n: int, width: int = 8) -> str:
    """Bit-by-bit trace of converting `n` to Gray code (n XOR (n >> 1))."""
    shifted = n >> 1
    g = binary_to_gray(n)
    lines = []
    lines.append(f"Binary to Gray: g = n XOR (n >> 1)")
    lines.append("")
    lines.append(f"n            = {n:0{width}b}  ({n})")
    lines.append(f"n >> 1       = {shifted:0{width}b}  ({shifted})")
    lines.append(f"n XOR (n>>1) = {g:0{width}b}  ({g})")
    lines.append("")
    lines.append(
        "Why this matters: consecutive Gray-coded values always differ by "
        "exactly one bit, unlike plain binary (e.g. 3 -> 4 flips 3 bits in "
        "binary but only 1 in Gray code). This avoids glitches when reading "
        "a rotary encoder or transitioning states in async digital logic."
    )
    return "\n".join(lines)


def explain_fixed_point(value: float, q_format: str) -> str:
    """Step-by-step trace of converting a float to Q-format fixed-point."""
    int_bits, frac_bits = parse_q_format(q_format)
    width = int_bits + frac_bits
    scale = 1 << frac_bits
    raw_max = (1 << (width - 1)) - 1
    raw_min = -(1 << (width - 1))
    raw_unclamped = round(value * scale)

    lines = []
    lines.append(f"{q_format}: {int_bits} integer bit(s) (incl. sign) + {frac_bits} fractional bits")
    lines.append(f"Total width: {width} bits, two's complement. Scale factor: 2^{frac_bits} = {scale}")
    lines.append(f"Representable range: [{raw_min / scale}, {raw_max / scale}]")
    lines.append("")
    lines.append(f"value x scale = {value} x {scale} = {value * scale}")
    lines.append(f"round(...)    = {raw_unclamped}")

    if raw_unclamped > raw_max or raw_unclamped < raw_min:
        lines.append(f"OUT OF RANGE for {q_format} (valid raw range: [{raw_min}, {raw_max}])")
    else:
        raw_bits = raw_unclamped & ((1 << width) - 1)
        lines.append(f"Raw {q_format} value: {raw_unclamped} (0x{raw_bits:0{(width + 3) // 4}X})")
        lines.append(f"Round trip check: {raw_unclamped} / {scale} = {raw_unclamped / scale}")

    return "\n".join(lines)
