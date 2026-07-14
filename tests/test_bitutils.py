import pytest

from bitlab.bitutils import (
    flip_bit,
    get_bit,
    has_odd_parity,
    popcount,
    reflect,
    rotate_left,
    rotate_right,
    set_bit,
)


def test_popcount():
    assert popcount(0b0) == 0
    assert popcount(0b1011) == 3
    assert popcount(0xFF) == 8


def test_popcount_rejects_negative():
    with pytest.raises(ValueError):
        popcount(-1)


def test_has_odd_parity():
    assert has_odd_parity(0b001) is True
    assert has_odd_parity(0b011) is False


def test_get_set_flip_bit():
    assert get_bit(0b1010, 1) == 1
    assert get_bit(0b1010, 0) == 0
    assert set_bit(0b0000, 2, 1) == 0b0100
    assert set_bit(0b1111, 2, 0) == 0b1011
    assert flip_bit(0b1010, 0) == 0b1011


def test_reflect():
    assert reflect(0b1100, 4) == 0b0011
    assert reflect(0b10000000, 8) == 0b00000001
    assert reflect(0x00, 8) == 0x00


def test_rotate_left_right():
    assert rotate_left(0b1000_0001, 1, 8) == 0b0000_0011
    assert rotate_right(0b1000_0001, 1, 8) == 0b1100_0000
    # full rotation returns the original value
    assert rotate_left(0b10110, 5, 5) == 0b10110
