"""Low-level bit helpers shared across every bitlab submodule.

These are foundational operations used by parity, crc, and future
submodules (register field mapping, endianness, etc).
"""

from __future__ import annotations

import random


def popcount(n: int) -> int:
    """Counts the number of 1-bits in a non-negative integer."""
    if n < 0:
        raise ValueError("popcount expects a non-negative integer")
    return bin(n).count("1")


def has_odd_parity(n: int) -> bool:
    """Returns True if `n` has an odd number of 1-bits."""
    return popcount(n) % 2 == 1


def get_bit(n: int, position: int) -> int:
    """Extracts the bit at `position` (0 = least significant) from `n`."""
    return (n >> position) & 1


def set_bit(n: int, position: int, bit: int) -> int:
    """Returns a copy of `n` with the bit at `position` set to `bit` (0 or 1)."""
    if bit:
        return n | (1 << position)
    return n & ~(1 << position)


def flip_bit(n: int, position: int) -> int:
    """Flips (inverts) the bit at `position` in `n`."""
    return n ^ (1 << position)


def reflect(value: int, width: int) -> int:
    """Reverses the lowest `width` bits of `value` (bit-mirror).

    Used throughout CRC algorithms (refin/refout) and relevant to Gray-code
    style bit-order tricks. Example: reflect(0b1100, 4) -> 0b0011.
    """
    result = 0
    for _ in range(width):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result


def rotate_left(value: int, amount: int, width: int) -> int:
    """Rotates `value` left by `amount` bits within a `width`-bit register."""
    amount %= width
    mask = (1 << width) - 1
    value &= mask
    return ((value << amount) | (value >> (width - amount))) & mask


def rotate_right(value: int, amount: int, width: int) -> int:
    """Rotates `value` right by `amount` bits within a `width`-bit register."""
    amount %= width
    mask = (1 << width) - 1
    value &= mask
    return ((value >> amount) | (value << (width - amount))) & mask


def random_bit_position(width: int) -> int:
    """Returns a random bit position in [0, width) using the `random` module
    (not cryptographically secure)."""
    return random.randrange(width)
