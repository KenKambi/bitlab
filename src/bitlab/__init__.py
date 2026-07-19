"""bitlab: a toolkit for embedded systems, binary data, and digital
communications.

Organized as submodules by domain rather than one flat namespace:

    from bitlab.parity import get_parity_bit, encode_hamming, decode_hamming
    from bitlab.crc import crc8, crc16, crc32, explain, export_c
    from bitlab.registers import Register, explain, export_c
    from bitlab.arch import decompose, swap_endianness, binary_to_gray, float_to_q
    from bitlab.comms import cobs_encode, cobs_decode, explain_cobs, export_c
    from bitlab.ecc import rs_encode, rs_decode, explain_rs_encode, export_c_encoder
    from bitlab.bitutils import popcount, rotate_left, reflect

`import bitlab` alone also gives you `bitlab.parity`, `bitlab.crc`,
`bitlab.registers`, `bitlab.arch`, `bitlab.comms`, `bitlab.ecc`, and
`bitlab.bitutils` as attributes, e.g. `bitlab.crc.crc32(b"...")`.
"""

from . import arch, bitutils, comms, crc, ecc, parity, registers

__version__ = "1.0.0"

__all__ = [
    "bitutils",
    "parity",
    "crc",
    "registers",
    "arch",
    "comms",
    "ecc",
    "__version__",
]
