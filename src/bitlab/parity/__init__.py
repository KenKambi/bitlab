"""Parity bit checking and Hamming(7,4) single-bit error correction."""

from .hamming import HammingDecodeResult, decode_hamming, encode_hamming
from .parity import (
    ParityType,
    append_parity,
    check_parity,
    check_parity_array,
    compute_message_parity,
    flip_random_bit,
    generate_parity_array,
    get_parity_bit,
)

__all__ = [
    "ParityType",
    "get_parity_bit",
    "append_parity",
    "check_parity",
    "generate_parity_array",
    "check_parity_array",
    "compute_message_parity",
    "flip_random_bit",
    "HammingDecodeResult",
    "encode_hamming",
    "decode_hamming",
]
