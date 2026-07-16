import pytest

from bitlab.arch import float_to_q, parse_q_format, q_range, q_to_float


def test_parse_q_format():
    assert parse_q_format("Q8.8") == (8, 8)
    assert parse_q_format("Q1.15") == (1, 15)


def test_parse_q_format_rejects_bad_input():
    with pytest.raises(ValueError):
        parse_q_format("8.8")
    with pytest.raises(ValueError):
        parse_q_format("Qfoo")


def test_q1_15_range():
    lo, hi = q_range("Q1.15")
    assert lo == -1.0
    assert hi == pytest.approx(0.999969, abs=1e-6)


def test_round_trip_within_range():
    for value in [0.5, -0.5, 0.999, -1.0, 0.0]:
        raw = float_to_q(value, "Q1.15")
        back = q_to_float(raw, "Q1.15")
        assert back == pytest.approx(value, abs=1e-4)


def test_q8_8_common_control_format():
    raw = float_to_q(3.14159, "Q8.8")
    assert q_to_float(raw, "Q8.8") == pytest.approx(3.14159, abs=0.01)


def test_out_of_range_raises_by_default():
    with pytest.raises(ValueError):
        float_to_q(1.5, "Q1.15")


def test_out_of_range_saturates_when_requested():
    lo, hi = q_range("Q1.15")
    assert q_to_float(float_to_q(1.5, "Q1.15", saturate=True), "Q1.15") == pytest.approx(hi, abs=1e-4)
    assert q_to_float(float_to_q(-1.5, "Q1.15", saturate=True), "Q1.15") == pytest.approx(lo, abs=1e-4)


def test_q_to_float_rejects_raw_out_of_range():
    with pytest.raises(ValueError):
        q_to_float(999999, "Q1.15")
