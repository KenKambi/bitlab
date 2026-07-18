# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned
- Reed-Solomon burst error correction (`bitlab.ecc`) — planned as a later,
  dedicated release given its complexity.

## [0.4.0] - 18-07-2026

### Added
- **New `bitlab.comms` submodule**: protocol framing.
  - **COBS** (`cobs.py`): `cobs_encode`/`cobs_decode` (Consistent Overhead
    Byte Stuffing) — removes all zero bytes from a payload so a single 0x00
    can be used as an unambiguous frame delimiter on a serial link, with at
    most 1 byte of overhead per 254 bytes of payload. `cobs_frame`/
    `cobs_unframe` convenience wrappers add/strip the trailing delimiter.
  - Verified against the published reference test vectors (Cheshire &
    Baker, IEEE/ACM ToN 1999), plus thousands of randomized round-trip
    property tests, including the 254-byte block-length boundary.
  - `cobs_decode` rejects malformed input: a zero byte where a length byte
    is expected, a truncated final block, *and* a zero byte found inside a
    block's data — the last of which can only indicate corrupted input,
    since a valid encoder never places one there.
  - `explain_cobs(data, max_blocks=6)`: step-by-step block-by-block trace,
    generated from the same code path as the real encoder so it can't
    drift out of sync with the actual output.
  - `export_c(encode_fn_name=..., decode_fn_name=...)`: standalone C99
    encode/decode functions. Unlike `crc`/`registers`, there's no
    per-config table to generate here — it emits a fixed, well-tested
    reference implementation, validated by compiling with `gcc` and
    property-testing the compiled binary against the Python implementation
    across randomized inputs.
- `bitlab comms cobs-encode|cobs-decode|cobs-explain|export-c` CLI
  subcommands.
- 31 new tests (150 total).

## [0.3.0] - 16-07-2026

### Added
- **New `bitlab.arch` submodule**: computer architecture toolkit.
  - **IEEE 754 deconstruction** (`ieee754.py`): `decompose(value, width=32|64)`
    breaks a float into sign/exponent/mantissa fields and classifies it
    (normal, subnormal, zero, infinity, nan); `compose(...)` rebuilds a
    float from raw fields; `to_bits`/`from_bits` for the raw bit pattern.
    Built on Python's `struct` module (the platform's native IEEE 754
    implementation) rather than reimplemented float math, so special values
    can't drift from correct behavior.
  - **Endianness** (`endianness.py`): `swap_endianness(value, width_bytes)`,
    plus `to_big_endian`/`to_little_endian`/`to_bytes`/`from_bytes` helpers.
  - **Gray code** (`gray.py`): `binary_to_gray`/`gray_to_binary`. Verified
    against the actual property Gray code exists for — every pair of
    consecutive values differs by exactly one bit — not just round-trip
    correctness.
  - **Q-format fixed-point** (`fixed_point.py`): `float_to_q`/`q_to_float`
    for Qm.n fixed-point conversion (e.g. `"Q1.15"`, `"Q8.8"`), with range
    checking and optional saturation, for MCUs without an FPU.
  - `explain_float`, `explain_endianness`, `explain_gray`,
    `explain_fixed_point`: step-by-step traces for each topic, following
    the same Compute/Explain pattern as `crc` and `registers`.
  - `export_c_endian_swap(width_bytes)` and `export_c_fixed_point(q_format)`:
    C99 code generation for the two topics with genuine embedded-C payoff.
    (IEEE 754 and Gray code are intentionally not exported to C — see the
    `codegen.py` module docstring for why.) Both validated by compiling the
    generated C with `gcc` and comparing against Python.
- `bitlab arch float|endian|gray-encode|gray-decode|q-encode|q-decode` CLI
  subcommands.
- 42 new tests (119 total).

### Changed
- Package version bumped to 0.3.0.

## [0.2.0] - 15-07-2026

### Added
- **New `bitlab.registers` submodule**: hardware register bit-field
  mapping, the signature embedded-dev feature.
  - `Register(name, size_bits=8)` — define a register's layout with
    `add_field(name, bit_index=...)` or `add_field(name, bit_range=(start, end))`.
    Validates overlapping fields and out-of-bounds fields at definition time.
  - `pack(**values)` / `unpack(raw)` — convert between named field values
    and a raw integer.
  - `get_field(raw, name)` / `set_field(raw, name, value)` — read/modify a
    single field via read-modify-write, preserving other bits.
  - `reserved_ranges()` — reports unassigned bit ranges.
  - `explain(reg, **values)`: datasheet-style bit diagram, field list, and
    (when field values are given) a step-by-step pack trace.
  - `export_c(reg, style="defines"|"struct")`:
    - `"defines"` (default) — portable `#define` position/mask macros plus
      `SET_`/`GET_` helper macros. Recommended: plain bitwise ops behave
      identically on every compiler/target.
    - `"struct"` — a C bit-field struct, with an explicit comment noting
      that C leaves bit-field allocation order implementation-defined
      (C99 6.7.2.1p10), so exact hardware bit placement should be verified
      against your compiler's documentation.
  - Both C export styles are validated by actually compiling the generated
    code with `gcc` and comparing the result to Python's `pack()`.
- `bitlab registers explain` and `bitlab registers export-c` CLI
  subcommands, using a `--field NAME:BIT` / `NAME:START-END` syntax.
- 21 new tests (77 total), including compiled-C correctness checks for both
  export styles.

### Changed
- Package version bumped to 0.2.0.

## [0.1.0] - 14-07-2026

### Added
- **Renamed the project from `parity-toolkit` to `bitlab`**, and
  restructured it as submodules under one umbrella package rather than a
  flat namespace, to give the project room to grow beyond parity:
  ```
  bitlab/
  ├── bitutils/   # foundational bit ops shared by every submodule
  ├── parity/     # parity bit checking + Hamming(7,4)
  └── crc/        # new in this release
  ```
- **New `bitlab.crc` submodule**: CRC generation, checking, explanation, and
  C code export.
  - `crc8()`, `crc16(variant="ccitt"|"modbus")`, `crc32()` convenience
    functions for the most common industry variants.
  - Generic `crc(data, config)` for custom polynomials via `CRCConfig`.
  - Built-in presets — `CRC8_SMBUS`, `CRC16_CCITT_FALSE`, `CRC16_MODBUS`,
    `CRC32_ISO_HDLC` — each verified against its published CRC-catalogue
    check value (the CRC of `b"123456789"`).
  - `explain(data, config)`: step-by-step trace of the real bitwise
    algorithm, for teaching/learning how CRC actually works.
  - `export_c(config, function_name=None)`: exports a table-driven C99
    implementation. The embedded lookup table is generated by the same code
    used internally by the fast Python path, and is validated by actually
    compiling the generated C with `gcc` and checking its output against
    the CRC catalogue in the test suite.
  - `compute_bitwise()` / `compute_table()` / `build_table()` / `self_test()`
    as lower-level building blocks.
- **New `bitlab.bitutils` submodule**: `popcount`, `has_odd_parity`,
  `get_bit`/`set_bit`/`flip_bit`, `reflect`, `rotate_left`/`rotate_right`,
  promoted out of the old parity-only utils module so they're shared
  foundational building blocks for `parity`, `crc`, and future submodules.
- Unified `bitlab` CLI covering `parity`, `hamming`, and `crc` subcommands
  (previously `parity-toolkit` had its own separate CLI).
- 56 tests total, including property-based cross-validation of the bitwise
  vs. table-driven CRC implementations and end-to-end compilation of
  generated C source.

### Changed
- `parity_toolkit.parity` → `bitlab.parity.parity` (same public API).
- `parity_toolkit.hamming` → `bitlab.parity.hamming` (same public API).
- Low-level bit helpers moved from `parity_toolkit.utils` to
  `bitlab.bitutils`.

### Migration from `parity-toolkit`
```diff
- from parity_toolkit import get_parity_bit, encode_hamming, decode_hamming
+ from bitlab.parity import get_parity_bit, encode_hamming, decode_hamming
```
```diff
- parity-toolkit bit 0b1011 --type even --width 4
+ bitlab parity bit 0b1011 --type even --width 4
```
The function signatures and behavior are unchanged — only the import path
and CLI command prefix moved.

---

## Prior history (as `parity-toolkit`, pre-rename)

### [0.1.0] - 2026-07-13 (parity-toolkit, superseded)
- Initial release: `get_parity_bit`, `append_parity`, `check_parity`,
  `generate_parity_array`, `check_parity_array`, `compute_message_parity`,
  `flip_random_bit`.
- Hamming(7,4) single-bit error correction: `encode_hamming`,
  `decode_hamming`.
- `parity-toolkit` CLI.

[Unreleased]: https://github.com/KenKambi/bitlab/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/KenKambi/bitlab/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/KenKambi/bitlab/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/KenKambi/bitlab/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/KenKambi/bitlab/releases/tag/v0.1.0
