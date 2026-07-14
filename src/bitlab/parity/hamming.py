"""Hamming(7,4) single-error-correcting code.

Encodes 4 data bits into a 7-bit codeword using 3 parity bits, positioned
(1-indexed) as:
    bit 1 = p1, bit 2 = p2, bit 3 = d1, bit 4 = p3, bit 5 = d2, bit 6 = d3, bit 7 = d4

p1 covers bits 1,3,5,7
p2 covers bits 2,3,6,7
p3 covers bits 4,5,6,7

This is the classic textbook layout, so codewords produced here match what
you'd compute by hand on paper.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HammingDecodeResult:
    """Result of decoding a 7-bit Hamming codeword."""

    data: int
    """The 4 recovered data bits, packed as d1d2d3d4 -> value 0-15."""

    error_position: int
    """1-indexed position of the corrected bit, or 0 if no error was found."""

    corrected: bool
    """True if a single-bit error was detected (and corrected)."""

    codeword: int
    """The (possibly corrected) 7-bit codeword."""


def _bit_at(codeword: int, position_1_indexed: int) -> int:
    # Bit 1 (1-indexed) is stored as the MSB of a 7-bit value.
    shift = 7 - position_1_indexed
    return (codeword >> shift) & 1


def _with_bit(codeword: int, position_1_indexed: int, bit: int) -> int:
    shift = 7 - position_1_indexed
    if bit:
        return codeword | (1 << shift)
    return codeword & ~(1 << shift)


def encode_hamming(data: int) -> int:
    """Encodes 4 data bits (0-15, interpreted as d1 d2 d3 d4 MSB-first) into
    a 7-bit Hamming codeword."""
    if data < 0 or data > 0b1111:
        raise ValueError("encode_hamming expects a 4-bit value (0-15)")

    d1 = (data >> 3) & 1
    d2 = (data >> 2) & 1
    d3 = (data >> 1) & 1
    d4 = data & 1

    codeword = 0
    codeword = _with_bit(codeword, 3, d1)
    codeword = _with_bit(codeword, 5, d2)
    codeword = _with_bit(codeword, 6, d3)
    codeword = _with_bit(codeword, 7, d4)

    p1 = d1 ^ d2 ^ d4  # covers 1,3,5,7
    p2 = d1 ^ d3 ^ d4  # covers 2,3,6,7
    p3 = d2 ^ d3 ^ d4  # covers 4,5,6,7

    codeword = _with_bit(codeword, 1, p1)
    codeword = _with_bit(codeword, 2, p2)
    codeword = _with_bit(codeword, 4, p3)

    return codeword


def decode_hamming(codeword: int) -> HammingDecodeResult:
    """Decodes a 7-bit Hamming codeword, detecting and correcting a
    single-bit error if present."""
    if codeword < 0 or codeword > 0b1111111:
        raise ValueError("decode_hamming expects a 7-bit value (0-127)")

    bits = [0] + [_bit_at(codeword, i) for i in range(1, 8)]

    c1 = bits[1] ^ bits[3] ^ bits[5] ^ bits[7]
    c2 = bits[2] ^ bits[3] ^ bits[6] ^ bits[7]
    c3 = bits[4] ^ bits[5] ^ bits[6] ^ bits[7]

    error_position = (c1 << 0) | (c2 << 1) | (c3 << 2)

    corrected = False
    fixed_codeword = codeword
    if error_position != 0:
        bad_bit = _bit_at(codeword, error_position)
        fixed_codeword = _with_bit(codeword, error_position, bad_bit ^ 1)
        corrected = True

    d1 = _bit_at(fixed_codeword, 3)
    d2 = _bit_at(fixed_codeword, 5)
    d3 = _bit_at(fixed_codeword, 6)
    d4 = _bit_at(fixed_codeword, 7)
    data = (d1 << 3) | (d2 << 2) | (d3 << 1) | d4

    return HammingDecodeResult(
        data=data,
        error_position=error_position,
        corrected=corrected,
        codeword=fixed_codeword,
    )
