"""Protocol framing for serial/byte-stream links.

Quick start:
    >>> from bitlab.comms import cobs_encode, cobs_decode
    >>> encoded = cobs_encode(b"hello\\x00world")
    >>> 0x00 in encoded
    False
    >>> cobs_decode(encoded) == b"hello\\x00world"
    True

Framing convenience (adds/strips the 0x00 delimiter for you):
    >>> from bitlab.comms import cobs_frame, cobs_unframe
    >>> wire_bytes = cobs_frame(b"hello\\x00world")
    >>> cobs_unframe(wire_bytes) == b"hello\\x00world"
    True

Educational trace:
    >>> from bitlab.comms import explain_cobs
    >>> print(explain_cobs(b"\\x11\\x22\\x00\\x33"))

Export to C:
    >>> from bitlab.comms import export_c
    >>> print(export_c())
"""

from .cobs import cobs_decode, cobs_encode, cobs_frame, cobs_unframe
from .codegen import export_c
from .explain import explain_cobs

__all__ = [
    "cobs_encode",
    "cobs_decode",
    "cobs_frame",
    "cobs_unframe",
    "explain_cobs",
    "export_c",
]
