"""CRC (Cyclic Redundancy Check) generation, checking, explanation, and C
code export.

Quick start:
    >>> from bitlab.crc import crc32
    >>> hex(crc32(b"123456789"))
    '0xcbf43926'

Custom polynomial:
    >>> from bitlab.crc import crc, CRCConfig
    >>> config = CRCConfig("my-crc", 16, 0x8005, 0xFFFF, True, True, 0x0000, 0x4B37)
    >>> crc(b"123456789", config)

Educational trace:
    >>> from bitlab.crc import explain, CRC8_SMBUS
    >>> print(explain(b"AB", CRC8_SMBUS))

Export to C for firmware use:
    >>> from bitlab.crc import export_c, CRC32_ISO_HDLC
    >>> print(export_c(CRC32_ISO_HDLC))
"""

from .codegen import export_c
from .engine import build_table, compute, compute_bitwise, compute_table, self_test
from .explain import explain
from .functions import crc, crc8, crc16, crc32
from .presets import (
    CRC8_SMBUS,
    CRC16_CCITT_FALSE,
    CRC16_MODBUS,
    CRC32_ISO_HDLC,
    CRCConfig,
)

__all__ = [
    "CRCConfig",
    "CRC8_SMBUS",
    "CRC16_CCITT_FALSE",
    "CRC16_MODBUS",
    "CRC32_ISO_HDLC",
    "crc",
    "crc8",
    "crc16",
    "crc32",
    "compute",
    "compute_bitwise",
    "compute_table",
    "build_table",
    "self_test",
    "explain",
    "export_c",
]
