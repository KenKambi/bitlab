import re

from bitlab.arch import (
    explain_endianness,
    explain_fixed_point,
    explain_float,
    explain_gray,
    float_to_q,
    swap_endianness,
)


def test_explain_float_contains_classification_and_value():
    trace = explain_float(0.15625, width=32)
    assert "0.15625" in trace
    assert "normal" in trace


def test_explain_float_handles_special_values_without_crashing():
    for value in [0.0, -0.0, float("inf"), float("-inf"), float("nan")]:
        trace = explain_float(value)
        assert isinstance(trace, str) and len(trace) > 0


def test_explain_endianness_matches_actual_swap():
    trace = explain_endianness(0x12345678, 4)
    match = re.search(r"Result: 0x([0-9A-Fa-f]+)", trace)
    assert match
    assert int(match.group(1), 16) == swap_endianness(0x12345678, 4)


def test_explain_gray_mentions_single_bit_property():
    trace = explain_gray(0b1011, width=8)
    assert "one bit" in trace


def test_explain_fixed_point_matches_actual_conversion():
    trace = explain_fixed_point(0.5, "Q1.15")
    match = re.search(r"Raw Q1\.15 value: (-?\d+)", trace)
    assert match
    assert int(match.group(1)) == float_to_q(0.5, "Q1.15")


def test_explain_fixed_point_reports_out_of_range():
    trace = explain_fixed_point(1.5, "Q1.15")
    assert "OUT OF RANGE" in trace
