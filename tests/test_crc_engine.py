import random

import pytest

from bitlab.crc.engine import build_table, compute_bitwise, compute_table, self_test
from bitlab.crc.presets import (
    CRC8_SMBUS,
    CRC16_CCITT_FALSE,
    CRC16_MODBUS,
    CRC32_ISO_HDLC,
)

ALL_PRESETS = [CRC8_SMBUS, CRC16_CCITT_FALSE, CRC16_MODBUS, CRC32_ISO_HDLC]


@pytest.mark.parametrize("config", ALL_PRESETS, ids=lambda c: c.name)
def test_matches_published_catalog_check_value(config):
    """Every preset must reproduce its published CRC-catalogue check value
    (the CRC of b"123456789") under both implementations."""
    assert self_test(config) is True


@pytest.mark.parametrize("config", ALL_PRESETS, ids=lambda c: c.name)
def test_bitwise_and_table_agree_on_random_data(config):
    """The fast table-driven path must always agree with the canonical
    bitwise reference implementation."""
    random.seed(1234)
    table = build_table(config)
    for _ in range(200):
        length = random.randint(0, 64)
        data = bytes(random.randrange(256) for _ in range(length))
        assert compute_bitwise(data, config) == compute_table(data, config, table)


@pytest.mark.parametrize("config", ALL_PRESETS, ids=lambda c: c.name)
def test_empty_input(config):
    """CRC of empty data should be well-defined and consistent across
    implementations."""
    assert compute_bitwise(b"", config) == compute_table(b"", config)


def test_build_table_has_256_entries():
    for config in ALL_PRESETS:
        table = build_table(config)
        assert len(table) == 256
        mask = (1 << config.width) - 1
        assert all(0 <= v <= mask for v in table)


def test_different_data_produces_different_crc():
    # Not a formal guarantee, but a basic sanity check that the CRC isn't
    # trivially constant.
    a = compute_table(b"hello", CRC32_ISO_HDLC)
    b = compute_table(b"world", CRC32_ISO_HDLC)
    assert a != b
