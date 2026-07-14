import pytest

from bitlab.crc import CRCConfig, crc, crc8, crc16, crc32

CHECK = b"123456789"


def test_crc8_check_value():
    assert crc8(CHECK) == 0xF4


def test_crc16_ccitt_check_value():
    assert crc16(CHECK, variant="ccitt") == 0x29B1


def test_crc16_modbus_check_value():
    assert crc16(CHECK, variant="modbus") == 0x4B37


def test_crc16_unknown_variant_raises():
    with pytest.raises(ValueError):
        crc16(CHECK, variant="bogus")


def test_crc32_check_value():
    assert crc32(CHECK) == 0xCBF43926


def test_generic_crc_with_preset_name():
    assert crc(CHECK, "crc32") == 0xCBF43926
    assert crc(CHECK, "crc8") == 0xF4


def test_generic_crc_with_unknown_preset_name_raises():
    with pytest.raises(ValueError):
        crc(CHECK, "not-a-real-preset")


def test_generic_crc_with_custom_config():
    # Re-derive CRC-16/MODBUS by hand to prove custom configs work.
    custom = CRCConfig(
        name="custom-modbus-clone",
        width=16,
        poly=0x8005,
        init=0xFFFF,
        refin=True,
        refout=True,
        xorout=0x0000,
        check=0x4B37,
    )
    assert crc(CHECK, custom) == 0x4B37
