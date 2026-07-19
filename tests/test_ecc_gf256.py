import pytest

from bitlab.ecc.gf256 import gf_div, gf_inverse, gf_mul, gf_pow


def test_multiplicative_inverse_holds_for_all_nonzero_elements():
    for a in range(1, 256):
        assert gf_mul(a, gf_inverse(a)) == 1


def test_mul_by_zero_is_zero():
    for a in range(256):
        assert gf_mul(a, 0) == 0
        assert gf_mul(0, a) == 0


def test_mul_is_commutative():
    for a in (0, 1, 2, 5, 100, 255):
        for b in (0, 1, 3, 77, 200):
            assert gf_mul(a, b) == gf_mul(b, a)


def test_div_is_inverse_of_mul():
    for a in range(1, 256):
        for b in (1, 2, 3, 100, 254):
            assert gf_div(gf_mul(a, b), b) == a


def test_div_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        gf_div(5, 0)


def test_pow_zero_is_one():
    for a in range(1, 256):
        assert gf_pow(a, 0) == 1


def test_pow_matches_repeated_mul():
    for a in (2, 3, 7, 100):
        expected = 1
        for _ in range(5):
            expected = gf_mul(expected, a)
        assert gf_pow(a, 5) == expected
