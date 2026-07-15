import re

from bitlab.registers import Register, explain


def make_reg() -> Register:
    reg = Register("UART_CR1", size_bits=8)
    reg.add_field("ENABLE", bit_index=0)
    reg.add_field("MODE", bit_range=(1, 3))
    reg.add_field("TXIE", bit_index=7)
    return reg


def test_explain_without_values_shows_layout():
    trace = explain(make_reg())
    assert "UART_CR1" in trace
    assert "ENABLE" in trace
    assert "MODE" in trace
    assert "TXIE" in trace
    assert "Reserved" in trace


def test_explain_with_values_matches_actual_pack():
    reg = make_reg()
    trace = explain(reg, ENABLE=1, MODE=5, TXIE=1)
    match = re.search(r"Final packed value: 0x([0-9A-Fa-f]+)", trace)
    assert match, "explain() must report the final packed value"
    assert int(match.group(1), 16) == reg.pack(ENABLE=1, MODE=5, TXIE=1)


def test_explain_without_values_has_no_pack_trace():
    trace = explain(make_reg())
    assert "Final packed value" not in trace
