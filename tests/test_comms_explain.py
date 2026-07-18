from bitlab.comms import cobs_encode, explain_cobs


def test_explain_output_contains_actual_encoded_result():
    data = bytes([0x11, 0x22, 0x00, 0x33])
    trace = explain_cobs(data)
    actual = cobs_encode(data)
    assert actual.hex(" ") in trace


def test_explain_notes_no_zero_byte_in_output():
    trace = explain_cobs(b"abc")
    assert "Contains a zero byte: no" in trace


def test_explain_truncates_many_blocks():
    # Force several zero-separated blocks to exceed max_blocks.
    data = bytes([1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7])
    trace = explain_cobs(data, max_blocks=2)
    assert "more blocks, same pattern" in trace


def test_explain_handles_empty_input():
    trace = explain_cobs(b"")
    assert "Input (0 bytes)" in trace
