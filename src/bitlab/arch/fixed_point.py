"""Q-format fixed-point conversion.

Many low-cost microcontrollers have no FPU, so firmware represents
fractional values as scaled integers instead: a Qm.n value is a two's
complement integer where the top `m` bits (including the sign bit) are the
integer part and the bottom `n` bits are the fractional part, with an
implicit scale factor of 2^n.

This module uses the common convention where `m` counts the sign bit as one
of the integer bits (so Q1.15 is a 16-bit format: 1 sign bit + 15 fractional
bits, range [-1.0, ~0.99997] -- the standard 16-bit audio/DSP format).
"""

from __future__ import annotations

from typing import Tuple


def parse_q_format(q_format: str) -> Tuple[int, int]:
    """Parses a "Qm.n" string into (integer_bits, fractional_bits).

    `integer_bits` includes the sign bit, per the TI/DSP convention (e.g.
    "Q1.15" -> (1, 15), a 16-bit signed format).
    """
    if not q_format.startswith("Q") or "." not in q_format:
        raise ValueError(f"Invalid Q-format string {q_format!r}, expected e.g. 'Q8.8' or 'Q1.15'")
    int_part, frac_part = q_format[1:].split(".", 1)
    try:
        integer_bits, fractional_bits = int(int_part), int(frac_part)
    except ValueError as exc:
        raise ValueError(f"Invalid Q-format string {q_format!r}") from exc
    if integer_bits < 1 or fractional_bits < 0:
        raise ValueError(f"Invalid Q-format string {q_format!r}: need >=1 integer bit")
    return integer_bits, fractional_bits


def _range_for(q_format: str):
    integer_bits, fractional_bits = parse_q_format(q_format)
    width = integer_bits + fractional_bits
    scale = 1 << fractional_bits
    raw_max = (1 << (width - 1)) - 1
    raw_min = -(1 << (width - 1))
    return width, scale, raw_min, raw_max


def float_to_q(value: float, q_format: str = "Q8.8", saturate: bool = False) -> int:
    """Converts `value` to a raw Q-format integer.

    Args:
        value: The value to convert.
        q_format: e.g. "Q8.8" (16-bit, 8 integer + 8 fractional) or "Q1.15"
            (16-bit audio format, range [-1.0, ~0.99997]).
        saturate: If True, out-of-range values are clamped to the nearest
            representable value instead of raising.
    """
    _, scale, raw_min, raw_max = _range_for(q_format)
    raw = round(value * scale)
    if raw < raw_min or raw > raw_max:
        if saturate:
            return max(raw_min, min(raw_max, raw))
        raise ValueError(
            f"{value} is out of range for {q_format} (raw={raw}, valid range=[{raw_min}, {raw_max}])"
        )
    return raw


def q_to_float(raw: int, q_format: str = "Q8.8") -> float:
    """Converts a raw Q-format integer back to a float."""
    width, scale, raw_min, raw_max = _range_for(q_format)
    if raw < raw_min or raw > raw_max:
        raise ValueError(f"raw value {raw} doesn't fit in {q_format} (range=[{raw_min}, {raw_max}])")
    return raw / scale


def q_range(q_format: str) -> Tuple[float, float]:
    """Returns the (min, max) representable float range for `q_format`."""
    _, scale, raw_min, raw_max = _range_for(q_format)
    return raw_min / scale, raw_max / scale
