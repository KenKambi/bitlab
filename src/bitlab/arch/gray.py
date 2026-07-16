"""Binary <-> Gray code conversion.

Gray code orders values so that any two consecutive values differ by
exactly one bit. This matters for rotary/quadrature encoders and
asynchronous digital logic, where a multi-bit binary transition
(e.g. 011 -> 100) can be briefly read as a completely wrong intermediate
value if the bits don't all change at exactly the same instant.
"""

from __future__ import annotations


def binary_to_gray(n: int) -> int:
    """Converts a standard binary value to its Gray code equivalent."""
    if n < 0:
        raise ValueError("binary_to_gray expects a non-negative integer")
    return n ^ (n >> 1)


def gray_to_binary(g: int) -> int:
    """Converts a Gray code value back to standard binary (the inverse of
    `binary_to_gray`)."""
    if g < 0:
        raise ValueError("gray_to_binary expects a non-negative integer")
    b = g
    shift = 1
    while g >> shift:
        b ^= g >> shift
        shift += 1
    return b
