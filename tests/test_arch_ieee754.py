import math

import pytest

from bitlab.arch import IEEE754Components, compose, decompose, from_bits, to_bits


def test_classic_textbook_example_32bit():
    """0.15625 = 1.25 x 2^-3, a commonly used teaching example."""
    c = decompose(0.15625, width=32)
    assert c.classification == "normal"
    assert c.sign == 0
    assert c.exponent == -3
    assert c.bits == 0x3E200000


def test_round_trip_various_values():
    for value in [1.0, -1.0, 3.14159, -0.001, 12345.6789, 2**100, 2**-100]:
        bits = to_bits(value, 32)
        assert from_bits(bits, 32) == pytest.approx(value, rel=1e-6)


def test_round_trip_64bit_is_exact_for_python_floats():
    for value in [1.0, -1.0, 3.14159265358979, 2**500, 2**-500]:
        bits = to_bits(value, 64)
        assert from_bits(bits, 64) == value


def test_zero_and_negative_zero():
    assert decompose(0.0).classification == "zero"
    assert decompose(0.0).sign == 0
    assert decompose(-0.0).classification == "zero"
    assert decompose(-0.0).sign == 1


def test_infinity():
    pos = decompose(float("inf"))
    neg = decompose(float("-inf"))
    assert pos.classification == "infinity"
    assert pos.sign == 0
    assert neg.classification == "infinity"
    assert neg.sign == 1


def test_nan():
    c = decompose(float("nan"))
    assert c.classification == "nan"


def test_subnormal():
    # smallest positive subnormal for 32-bit: 2^-149
    tiny = 2.0**-149
    c = decompose(tiny, width=32)
    assert c.classification == "subnormal"


def test_compose_is_inverse_of_decompose_for_normal_values():
    for value in [1.5, -42.25, 0.001, 999999.999]:
        c = decompose(value, width=32)
        rebuilt = compose(c.sign, c.exponent_raw, c.mantissa, width=32)
        assert rebuilt == pytest.approx(value, rel=1e-6)


def test_invalid_width_raises():
    with pytest.raises(ValueError):
        decompose(1.0, width=16)


def test_compose_validates_field_ranges():
    with pytest.raises(ValueError):
        compose(2, 0, 0, width=32)  # sign must be 0 or 1
    with pytest.raises(ValueError):
        compose(0, 999, 0, width=32)  # exponent_raw too large
    with pytest.raises(ValueError):
        compose(0, 0, 999999999, width=32)  # mantissa too large
