"""Reed-Solomon error correction over GF(256).

Reed-Solomon corrects *burst* errors -- clusters of consecutive corrupted
bytes, or scattered corruption anywhere in a block -- which simple parity
and even Hamming(7,4) can't handle. It's what QR codes, CDs/DVDs, RAID 6,
and deep-space telemetry (Voyager, CCSDS) actually use.

Quick start:
    >>> from bitlab.ecc import rs_encode, rs_decode
    >>> encoded = rs_encode(b"Hello, World!", nsym=10)
    >>> corrupted = bytearray(encoded)
    >>> corrupted[0] ^= 0xFF
    >>> corrupted[5] ^= 0xFF
    >>> bytes(rs_decode(bytes(corrupted), nsym=10)) == b"Hello, World!"
    True

`nsym` parity bytes correct up to `nsym // 2` byte errors anywhere in the
block (message + parity together must be at most 255 bytes -- the
fundamental limit of GF(256)).

Educational trace (encoding only -- see `explain.py` for why):
    >>> from bitlab.ecc import explain_rs_encode
    >>> print(explain_rs_encode(b"hi", nsym=4))

Export the encoder to C:
    >>> from bitlab.ecc import export_c_encoder
    >>> print(export_c_encoder(nsym=10))
"""

from .codegen import export_c_encoder
from .explain import explain_rs_encode
from .reed_solomon import MAX_BLOCK_SIZE, ReedSolomonError, generator_poly, rs_decode, rs_encode

__all__ = [
    "rs_encode",
    "rs_decode",
    "generator_poly",
    "ReedSolomonError",
    "MAX_BLOCK_SIZE",
    "explain_rs_encode",
    "export_c_encoder",
]
