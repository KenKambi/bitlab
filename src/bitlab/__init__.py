"""bitlab: a toolkit for embedded systems, binary data, and digital
communications.

Organized as submodules by domain rather than one flat namespace:

    from bitlab.parity import get_parity_bit, encode_hamming, decode_hamming
    from bitlab.crc import crc8, crc16, crc32, explain, export_c
    from bitlab.bitutils import popcount, rotate_left, reflect

`import bitlab` alone also gives you `bitlab.parity`, `bitlab.crc`, and
`bitlab.bitutils` as attributes, e.g. `bitlab.crc.crc32(b"...")`.
"""

from . import bitutils, crc, parity

__version__ = "0.1.0"

__all__ = ["bitutils", "parity", "crc", "__version__"]
