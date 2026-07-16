import pytest

from bitlab.arch import binary_to_gray, gray_to_binary


def _popcount(n: int) -> int:
    return bin(n).count("1")


def test_round_trip_all_8bit_values():
    for n in range(256):
        assert gray_to_binary(binary_to_gray(n)) == n


def test_consecutive_values_differ_by_exactly_one_bit():
    """The entire point of Gray code."""
    for n in range(255):
        diff = binary_to_gray(n) ^ binary_to_gray(n + 1)
        assert _popcount(diff) == 1


def test_zero_maps_to_zero():
    assert binary_to_gray(0) == 0
    assert gray_to_binary(0) == 0


def test_rejects_negative():
    with pytest.raises(ValueError):
        binary_to_gray(-1)
    with pytest.raises(ValueError):
        gray_to_binary(-1)
