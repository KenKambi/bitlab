import pytest

from bitlab.arch import from_bytes, swap_endianness, to_big_endian, to_bytes, to_little_endian


def test_swap_endianness_32bit():
    assert swap_endianness(0x12345678, 4) == 0x78563412


def test_swap_endianness_16bit():
    assert swap_endianness(0x1234, 2) == 0x3412


def test_swap_endianness_is_its_own_inverse():
    value = 0xDEADBEEF
    assert swap_endianness(swap_endianness(value, 4), 4) == value


def test_swap_endianness_rejects_negative():
    with pytest.raises(ValueError):
        swap_endianness(-1, 4)


def test_swap_endianness_rejects_oversized_value():
    with pytest.raises(ValueError):
        swap_endianness(0x1_0000_0000, 4)  # doesn't fit in 4 bytes


def test_to_big_endian_and_little_endian():
    assert to_big_endian(0x1234, 2) == b"\x12\x34"
    assert to_little_endian(0x1234, 2) == b"\x34\x12"


def test_to_bytes_and_from_bytes_round_trip():
    for byteorder in ("big", "little"):
        data = to_bytes(0xCAFEBABE, 4, byteorder=byteorder)
        assert from_bytes(data, byteorder=byteorder) == 0xCAFEBABE
