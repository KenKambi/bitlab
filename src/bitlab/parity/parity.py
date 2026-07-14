"""Parity bit generation, appending, and checking for integers, sequences,
and strings."""

from __future__ import annotations

from typing import List, Literal, Sequence

from ..bitutils import flip_bit, get_bit, popcount, random_bit_position, set_bit

ParityType = Literal["even", "odd"]


def get_parity_bit(value: int, type: ParityType = "even", bit_width: int = 8) -> int:
    """Computes the parity bit needed so that `value`'s 1-bit count (over
    `bit_width` bits) plus the parity bit satisfies the requested parity type.

    Args:
        value: The data value to compute parity for.
        type: 'even' (default) or 'odd'.
        bit_width: Number of bits of `value` to consider (default 8).
    """
    mask = (1 << bit_width) - 1
    ones = popcount(value & mask)
    is_odd = ones % 2 == 1

    if type == "even":
        return 1 if is_odd else 0
    return 0 if is_odd else 1


def append_parity(value: int, type: ParityType = "even", bit_width: int = 8) -> int:
    """Appends a parity bit to `value` as the most-significant bit (at
    position `bit_width`), returning the combined (bit_width + 1)-bit value.

    Example: append_parity(0b1011, 'even', 4) -> 0b11011 (parity bit = 1)
    """
    parity_bit = get_parity_bit(value, type, bit_width)
    return set_bit(value, bit_width, parity_bit)


def check_parity(
    value_with_parity: int, type: ParityType = "even", bit_width: int = 8
) -> bool:
    """Checks whether `value_with_parity` (a value that includes its parity
    bit at position `bit_width`) is internally consistent with the requested
    parity type. Returns False if a (single-bit) error is detected.
    """
    data_mask = (1 << bit_width) - 1
    data = value_with_parity & data_mask
    parity_bit = get_bit(value_with_parity, bit_width)
    expected = get_parity_bit(data, type, bit_width)
    return parity_bit == expected


def generate_parity_array(
    values: Sequence[int], type: ParityType = "even", bit_width: int = 8
) -> List[int]:
    """Generates a parity bit for each value (bit_width-wide) in a sequence."""
    return [get_parity_bit(v, type, bit_width) for v in values]


def check_parity_array(
    values_with_parity: Sequence[int], type: ParityType = "even", bit_width: int = 8
) -> List[bool]:
    """Checks parity for a sequence of values that already include their
    parity bit (see append_parity). Returns a list of booleans, one per input
    value."""
    return [check_parity(v, type, bit_width) for v in values_with_parity]


def compute_message_parity(message: str, type: ParityType = "even") -> int:
    """Computes a single overall parity bit for a whole message (string),
    based on the total 1-bit count across all UTF-8 code units. Useful as a
    cheap, whole-message integrity check (NOT a substitute for a real
    checksum/CRC on anything that matters).
    """
    ones = sum(popcount(b) for b in message.encode("utf-8"))
    is_odd = ones % 2 == 1
    if type == "even":
        return 1 if is_odd else 0
    return 0 if is_odd else 1


def flip_random_bit(value: int, bit_width: int = 8) -> int:
    """Flips a random bit within the lowest `bit_width` bits of `value`.
    Handy for simulating a single-bit transmission error when testing
    parity/Hamming code."""
    position = random_bit_position(bit_width)
    return flip_bit(value, position)
