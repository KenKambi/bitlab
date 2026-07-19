import pytest

from bitlab.ecc import rs_encode
from bitlab.ecc.explain import explain_rs_encode


def test_explain_final_output_matches_actual_encode():
    data = b"hello"
    nsym = 6
    trace = explain_rs_encode(data, nsym)
    actual = rs_encode(data, nsym)
    assert actual.hex(" ") in trace


def test_explain_rejects_empty_data():
    with pytest.raises(ValueError):
        explain_rs_encode(b"", nsym=4)


def test_explain_rejects_oversized_block():
    with pytest.raises(ValueError):
        explain_rs_encode(bytes(250), nsym=10)


def test_explain_mentions_correction_capacity():
    trace = explain_rs_encode(b"x", nsym=10)
    assert "corrects up to 5 byte errors" in trace
