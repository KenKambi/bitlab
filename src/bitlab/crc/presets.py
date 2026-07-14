"""CRC configuration presets.

Each preset's parameters (poly/init/refin/refout/xorout) and `check` value
come from the standard CRC catalogue (the CRC of the ASCII string
"123456789"). Every preset here is verified against that check value in the
test suite via `bitlab.crc.engine.self_test`, so you can trust these match
what real hardware/protocols expect — not just "a CRC that happens to run".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CRCConfig:
    """Parameters that fully define a CRC algorithm (the "Rocksoft model").

    Attributes:
        name: Human-readable name, e.g. "CRC-32/ISO-HDLC".
        width: Register width in bits (8, 16, or 32).
        poly: The generator polynomial, without its implicit leading term.
        init: Initial register value.
        refin: If True, each input byte is bit-reversed before processing.
        refout: If True, the final register is bit-reversed before xorout.
        xorout: Value XORed with the final register to produce the result.
        check: The known-correct CRC of b"123456789" for this configuration,
            used to self-test the engine against the published catalogue.
    """

    name: str
    width: int
    poly: int
    init: int
    refin: bool
    refout: bool
    xorout: int
    check: int


# CRC-8/SMBUS -- used in SMBus, some simple embedded checksums.
CRC8_SMBUS = CRCConfig(
    name="CRC-8/SMBUS",
    width=8,
    poly=0x07,
    init=0x00,
    refin=False,
    refout=False,
    xorout=0x00,
    check=0xF4,
)

# CRC-16/CCITT-FALSE -- widely used in firmware/bootloader integrity checks.
CRC16_CCITT_FALSE = CRCConfig(
    name="CRC-16/CCITT-FALSE",
    width=16,
    poly=0x1021,
    init=0xFFFF,
    refin=False,
    refout=False,
    xorout=0x0000,
    check=0x29B1,
)

# CRC-16/MODBUS -- the CRC used by the Modbus serial protocol.
CRC16_MODBUS = CRCConfig(
    name="CRC-16/MODBUS",
    width=16,
    poly=0x8005,
    init=0xFFFF,
    refin=True,
    refout=True,
    xorout=0x0000,
    check=0x4B37,
)

# CRC-32/ISO-HDLC -- the "standard" CRC-32 used by Ethernet, zlib/gzip, PNG.
CRC32_ISO_HDLC = CRCConfig(
    name="CRC-32/ISO-HDLC",
    width=32,
    poly=0x04C11DB7,
    init=0xFFFFFFFF,
    refin=True,
    refout=True,
    xorout=0xFFFFFFFF,
    check=0xCBF43926,
)

PRESETS = {
    "crc8": CRC8_SMBUS,
    "crc16-ccitt": CRC16_CCITT_FALSE,
    "crc16-modbus": CRC16_MODBUS,
    "crc32": CRC32_ISO_HDLC,
}
