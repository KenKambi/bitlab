import re

from bitlab.crc.engine import compute
from bitlab.crc.explain import explain
from bitlab.crc.presets import CRC8_SMBUS, CRC16_MODBUS, CRC32_ISO_HDLC


def _extract_final_crc(trace: str) -> int:
    match = re.search(r"Final CRC: 0x([0-9A-Fa-f]+)", trace)
    assert match, "explain() output must contain a 'Final CRC: 0x...' line"
    return int(match.group(1), 16)


def test_explain_matches_actual_computed_value_crc8():
    data = b"AB"
    trace = explain(data, CRC8_SMBUS)
    assert _extract_final_crc(trace) == compute(data, CRC8_SMBUS)


def test_explain_matches_actual_computed_value_crc32():
    data = b"123456789"
    trace = explain(data, CRC32_ISO_HDLC)
    assert _extract_final_crc(trace) == compute(data, CRC32_ISO_HDLC)


def test_explain_truncates_long_input():
    data = bytes(range(50))
    trace = explain(data, CRC16_MODBUS, max_bytes=3)
    assert "more bytes processed the same way" in trace


def test_explain_contains_algorithm_parameters():
    trace = explain(b"x", CRC32_ISO_HDLC)
    assert "CRC-32/ISO-HDLC" in trace
    assert "refin=True" in trace
