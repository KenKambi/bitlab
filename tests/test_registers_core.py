import pytest

from bitlab.registers import Register


def make_uart_cr1() -> Register:
    reg = Register("UART_CR1", size_bits=8)
    reg.add_field("ENABLE", bit_index=0, description="Peripheral enable")
    reg.add_field("MODE", bit_range=(1, 3), description="Operating mode")
    reg.add_field("TXIE", bit_index=7, description="TX interrupt enable")
    return reg


def test_pack_and_unpack_round_trip():
    reg = make_uart_cr1()
    raw = reg.pack(ENABLE=1, MODE=0b101, TXIE=1)
    assert raw == 0b10001011
    assert reg.unpack(raw) == {"ENABLE": 1, "MODE": 5, "TXIE": 1}


def test_pack_defaults_unspecified_fields_to_zero():
    reg = make_uart_cr1()
    assert reg.pack(ENABLE=1) == 0b00000001


def test_get_field():
    reg = make_uart_cr1()
    raw = reg.pack(MODE=0b110)
    assert reg.get_field(raw, "MODE") == 0b110


def test_set_field_preserves_other_bits():
    reg = make_uart_cr1()
    raw = reg.pack(ENABLE=1, MODE=0b111, TXIE=1)
    updated = reg.set_field(raw, "MODE", 0b010)
    assert reg.get_field(updated, "ENABLE") == 1
    assert reg.get_field(updated, "TXIE") == 1
    assert reg.get_field(updated, "MODE") == 0b010


def test_reserved_ranges():
    reg = make_uart_cr1()
    assert reg.reserved_ranges() == [(4, 6)]


def test_fully_packed_register_has_no_reserved_bits():
    reg = Register("FULL", size_bits=4)
    reg.add_field("A", bit_range=(0, 1))
    reg.add_field("B", bit_range=(2, 3))
    assert reg.reserved_ranges() == []


def test_overlapping_field_raises():
    reg = make_uart_cr1()
    with pytest.raises(ValueError, match="overlaps"):
        reg.add_field("BAD", bit_index=2)


def test_duplicate_field_name_raises():
    reg = make_uart_cr1()
    with pytest.raises(ValueError, match="already exists"):
        reg.add_field("ENABLE", bit_index=5)


def test_field_out_of_register_bounds_raises():
    reg = Register("SMALL", size_bits=4)
    with pytest.raises(ValueError, match="doesn't fit"):
        reg.add_field("TOO_BIG", bit_range=(2, 5))


def test_add_field_requires_exactly_one_of_bit_index_or_bit_range():
    reg = Register("R", size_bits=8)
    with pytest.raises(ValueError):
        reg.add_field("X")
    with pytest.raises(ValueError):
        reg.add_field("X", bit_index=0, bit_range=(1, 2))


def test_pack_rejects_unknown_field():
    reg = make_uart_cr1()
    with pytest.raises(ValueError, match="Unknown field"):
        reg.pack(NOT_A_FIELD=1)


def test_pack_rejects_out_of_range_value():
    reg = make_uart_cr1()
    with pytest.raises(ValueError, match="out of range"):
        reg.pack(MODE=8)  # MODE is 3 bits wide, max 7


def test_layout_is_msb_to_lsb():
    reg = make_uart_cr1()
    names = [f.name for f in reg.layout()]
    assert names == ["TXIE", "MODE", "ENABLE"]
