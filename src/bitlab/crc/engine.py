"""Generic, parameterized CRC engine.

Implements the standard "Rocksoft model" CRC algorithm: any CRC (CRC-8,
CRC-16, CRC-32, ...) can be described by (width, poly, init, refin, refout,
xorout). Two computation strategies are provided:

- `compute_bitwise`: the canonical, easy-to-verify reference algorithm.
  Processes one bit at a time. This is what `CRCConfig.check` is validated
  against, and what `explain()` walks through step by step.
- `compute_table`: a table-driven implementation (the same algorithm real
  hardware/firmware uses for speed). The lookup table is also what
  `codegen.export_c()` embeds in the generated C source, so the Python fast
  path and the exported C code are built from the exact same table.

Both strategies are cross-validated against each other and against published
CRC-catalogue check values in the test suite.
"""

from __future__ import annotations

from typing import List

from ..bitutils import reflect
from .presets import CRCConfig


def compute_bitwise(data: bytes, config: CRCConfig) -> int:
    """Computes a CRC using the canonical bit-by-bit algorithm.

    This is the reference implementation: simple enough to read and trust,
    at the cost of processing 8 shifts per input byte instead of 1 table
    lookup. Fine for typical prototyping payloads; use `compute_table` (or
    just `compute`, which picks the fast path automatically) for large data.
    """
    width = config.width
    mask = (1 << width) - 1
    topbit = 1 << (width - 1)
    reg = config.init & mask

    for byte in data:
        b = reflect(byte, 8) if config.refin else byte
        reg ^= (b << (width - 8)) & mask
        for _ in range(8):
            if reg & topbit:
                reg = ((reg << 1) ^ config.poly) & mask
            else:
                reg = (reg << 1) & mask

    if config.refout:
        reg = reflect(reg, width)
    return (reg ^ config.xorout) & mask


def build_table(config: CRCConfig) -> List[int]:
    """Builds the 256-entry lookup table for `config`.

    Two distinct table algorithms exist depending on whether the CRC
    processes bits MSB-first (refin=False) or LSB-first (refin=True); this
    picks the correct one automatically. The returned table is exactly what
    `codegen.export_c` embeds in generated C source.
    """
    width = config.width
    mask = (1 << width) - 1

    if config.refin:
        rpoly = reflect(config.poly, width)
        table = []
        for i in range(256):
            reg = i
            for _ in range(8):
                if reg & 1:
                    reg = (reg >> 1) ^ rpoly
                else:
                    reg = reg >> 1
            table.append(reg & mask)
        return table

    topbit = 1 << (width - 1)
    table = []
    for i in range(256):
        reg = i << (width - 8)
        for _ in range(8):
            if reg & topbit:
                reg = ((reg << 1) ^ config.poly) & mask
            else:
                reg = (reg << 1) & mask
        table.append(reg & mask)
    return table


def compute_table(data: bytes, config: CRCConfig, table: List[int] = None) -> int:
    """Computes a CRC using a lookup table (builds one if not supplied).

    Pass a pre-built table (from `build_table`) when computing many CRCs
    with the same config to avoid rebuilding it each call.
    """
    width = config.width
    mask = (1 << width) - 1
    if table is None:
        table = build_table(config)

    if config.refin:
        reg = reflect(config.init & mask, width)
        for byte in data:
            idx = (reg ^ byte) & 0xFF
            reg = ((reg >> 8) ^ table[idx]) & mask
        return (reg ^ config.xorout) & mask

    reg = config.init & mask
    shift = width - 8
    for byte in data:
        idx = ((reg >> shift) ^ byte) & 0xFF
        reg = ((reg << 8) ^ table[idx]) & mask
    if config.refout:
        reg = reflect(reg, width)
    return (reg ^ config.xorout) & mask


def compute(data: bytes, config: CRCConfig) -> int:
    """Computes a CRC using the fast table-driven path. This is what the
    `crc8`/`crc16`/`crc32` convenience functions and the generic `crc()`
    function call."""
    return compute_table(data, config)


def self_test(config: CRCConfig) -> bool:
    """Verifies `config` against its known check value (CRC of b"123456789"),
    using both the bitwise and table-driven implementations. Returns True
    only if both agree with `config.check`."""
    check_input = b"123456789"
    return (
        compute_bitwise(check_input, config) == config.check
        and compute_table(check_input, config) == config.check
    )
