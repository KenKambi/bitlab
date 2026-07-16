"""Endianness conversion for fixed-width integers.

Big-endian stores the most-significant byte first (network byte order);
little-endian stores the least-significant byte first (x86, most Cortex-M
configurations). Getting this wrong is a classic source of "the sensor
reading is off by a factor of 256" bugs.
"""

from __future__ import annotations


def swap_endianness(value: int, width_bytes: int) -> int:
    """Reverses the byte order of `value`, treated as an unsigned integer
    `width_bytes` wide.

    Example: swap_endianness(0x12345678, 4) -> 0x78563412
    """
    if value < 0:
        raise ValueError("swap_endianness expects an unsigned value")
    if value >= (1 << (width_bytes * 8)):
        raise ValueError(f"value doesn't fit in {width_bytes} bytes")
    data = value.to_bytes(width_bytes, byteorder="big")
    return int.from_bytes(data[::-1], byteorder="big")


def to_bytes(value: int, width_bytes: int, byteorder: str = "big") -> bytes:
    """Encodes `value` as `width_bytes` bytes in the given byte order
    ('big' or 'little'). Thin, explicit wrapper around `int.to_bytes` kept
    here so the whole endianness story lives in one place."""
    return value.to_bytes(width_bytes, byteorder=byteorder)


def from_bytes(data: bytes, byteorder: str = "big") -> int:
    """Decodes `data` into an integer using the given byte order."""
    return int.from_bytes(data, byteorder=byteorder)


def to_big_endian(value: int, width_bytes: int) -> bytes:
    """Encodes `value` as `width_bytes` big-endian bytes."""
    return to_bytes(value, width_bytes, "big")


def to_little_endian(value: int, width_bytes: int) -> bytes:
    """Encodes `value` as `width_bytes` little-endian bytes."""
    return to_bytes(value, width_bytes, "little")
