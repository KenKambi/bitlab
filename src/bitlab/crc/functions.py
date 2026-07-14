"""Convenience functions for the common CRC variants, plus a generic
parameterized entry point for custom polynomials."""

from __future__ import annotations

from typing import Union

from .engine import compute
from .presets import (
    CRC8_SMBUS,
    CRC16_CCITT_FALSE,
    CRC16_MODBUS,
    CRC32_ISO_HDLC,
    CRCConfig,
)


def crc8(data: bytes) -> int:
    """CRC-8/SMBUS of `data`."""
    return compute(data, CRC8_SMBUS)


def crc16(data: bytes, variant: str = "ccitt") -> int:
    """CRC-16 of `data`.

    Args:
        variant: 'ccitt' (CRC-16/CCITT-FALSE, default) or 'modbus'
            (CRC-16/MODBUS, used by the Modbus protocol).
    """
    if variant == "ccitt":
        return compute(data, CRC16_CCITT_FALSE)
    if variant == "modbus":
        return compute(data, CRC16_MODBUS)
    raise ValueError(f"Unknown CRC-16 variant: {variant!r} (expected 'ccitt' or 'modbus')")


def crc32(data: bytes) -> int:
    """CRC-32/ISO-HDLC of `data` (the CRC used by Ethernet, zlib, PNG)."""
    return compute(data, CRC32_ISO_HDLC)


def crc(data: bytes, config: Union[CRCConfig, str]) -> int:
    """Generic CRC entry point.

    Args:
        data: The bytes to checksum.
        config: Either a `CRCConfig` (for a fully custom polynomial) or the
            name of a built-in preset: 'crc8', 'crc16-ccitt', 'crc16-modbus',
            or 'crc32'.
    """
    if isinstance(config, str):
        from .presets import PRESETS

        if config not in PRESETS:
            raise ValueError(
                f"Unknown preset {config!r}. Available: {', '.join(PRESETS)}"
            )
        config = PRESETS[config]
    return compute(data, config)
