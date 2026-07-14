# bitlab

[![CI](https://github.com/KenKambi/bitlab/actions/workflows/ci.yml/badge.svg)](https://github.com/KenKambi/bitlab/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/bitlab.svg)](https://pypi.org/project/bitlab/)

A toolkit for embedded systems, binary data, and digital communications.

Built around the topics an Electronic & Computer Engineering degree
actually covers: digital logic, computer architecture, embedded systems,
and communications. Each domain is a self-contained submodule, so the
package can keep growing without becoming a junk drawer.

- Zero dependencies
- Type-hinted (PEP 561, ships a `py.typed` marker)
- One CLI: `bitlab`
- Production functions **and** step-by-step educational explanations, side by side
- CRC configs export directly to compiled, table-driven C — the same table your Python code uses

```
bitlab/
├── bitutils/   # foundational bit ops used by every other submodule
├── parity/     # parity bit checking + Hamming(7,4) error correction
└── crc/        # CRC-8/16/32, generic engine, explain(), export_c()
```

## Install

```bash
pip install bitlab
```

## `bitlab.crc` — CRC generation, checking, explanation, and C export

```python
from bitlab.crc import crc8, crc16, crc32

crc8(b"hello")              # CRC-8/SMBUS
crc16(b"hello")             # CRC-16/CCITT-FALSE (default)
crc16(b"hello", variant="modbus")  # CRC-16/MODBUS
crc32(b"hello")              # CRC-32/ISO-HDLC (Ethernet, zlib, PNG)
```

Every built-in preset is verified against its published CRC-catalogue check
value (the CRC of `b"123456789"`) in the test suite — these aren't "a CRC
that happens to run", they match what real hardware and protocols expect.

### Custom polynomials

```python
from bitlab.crc import crc, CRCConfig

my_crc = CRCConfig(
    name="my-custom-crc",
    width=16, poly=0x8005, init=0xFFFF,
    refin=True, refout=True, xorout=0x0000,
    check=0x4B37,  # CRC of b"123456789", for self-testing your config
)
crc(b"some data", my_crc)
```

### Step-by-step explanation (the same computation, narrated)

```python
from bitlab.crc import explain, CRC8_SMBUS

print(explain(b"AB", CRC8_SMBUS))
```

```
CRC algorithm: CRC-8/SMBUS
  width=8  poly=0x07  init=0x00  refin=False  refout=False  xorout=0x00

Input bytes (2 total): 41 42

Initial register: 0x00

Byte 0: 0x41 -> XORed in, register = 0x41
    bit 0: MSB=0 -> shift left -> 0x82
    bit 1: MSB=1 -> shift left, XOR polynomial -> 0x03
    ...

Final CRC: 0x87
```

`explain()` runs the real bitwise algorithm with a narration attached — it's
not a separate simplified explanation, so what you read is guaranteed to
match what `crc8`/`crc16`/`crc32` actually compute.

### Export to C

```python
from bitlab.crc import export_c, CRC32_ISO_HDLC

print(export_c(CRC32_ISO_HDLC, function_name="my_crc32"))
```

```c
#include <stdint.h>
#include <stddef.h>

static const uint32_t my_crc32_table[256] = {
    0x00000000, 0x77073096, 0xEE0E612C, 0x990951BA, ...
};

uint32_t my_crc32(const uint8_t *data, size_t len)
{
    uint32_t crc = 0xFFFFFFFFU;
    for (size_t i = 0; i < len; i++) {
        uint8_t idx = (uint8_t)(crc ^ data[i]);
        crc = (crc >> 8) ^ my_crc32_table[idx];
    }
    return (crc ^ 0xFFFFFFFFU);
}
```

The exported table is built by the exact same code Python's fast path
uses — the test suite actually compiles the generated C with `gcc` and
checks the output against the CRC catalogue, so this isn't just
"code that looks right."

## `bitlab.parity` — parity bits and Hamming(7,4)

```python
from bitlab.parity import get_parity_bit, append_parity, check_parity

get_parity_bit(0b1011, "even", 4)      # -> 1
append_parity(0b1011, "even", 4)       # -> 0b11011
check_parity(0b11011, "even", 4)       # -> True
```

```python
from bitlab.parity import encode_hamming, decode_hamming

codeword = encode_hamming(0b1101)
corrupted = codeword ^ 0b0000100        # simulate a single-bit flip
result = decode_hamming(corrupted)
# HammingDecodeResult(data=13, error_position=6, corrected=True, codeword=...)
```

See the full parity/Hamming API reference at the bottom of this file.

## `bitlab.bitutils` — shared low-level bit helpers

```python
from bitlab.bitutils import popcount, reflect, rotate_left, rotate_right

popcount(0b1011)           # -> 3
reflect(0b1100, 4)         # -> 0b0011 (bit-mirror, used internally by crc)
rotate_left(0b10000001, 1, 8)   # -> 0b00000011
```

## CLI

```bash
bitlab parity bit 0b1011 --type even --width 4
# -> 1

bitlab hamming encode 13
# -> 85 (0b1010101)

bitlab crc compute "123456789" --preset crc32
# -> 0xCBF43926 (3421780262)

bitlab crc explain "AB" --preset crc8
# -> step-by-step trace

bitlab crc export-c --preset crc32 --name my_crc32
# -> C source on stdout
```

Run `bitlab --help`, `bitlab crc --help`, etc. for full usage.

## API reference

### `bitlab.crc`

| Function | Description |
|---|---|
| `crc8(data)` | CRC-8/SMBUS. |
| `crc16(data, variant="ccitt")` | CRC-16/CCITT-FALSE or CRC-16/MODBUS. |
| `crc32(data)` | CRC-32/ISO-HDLC (Ethernet/zlib/PNG). |
| `crc(data, config)` | Generic entry point. `config` is a `CRCConfig` or a preset name string. |
| `explain(data, config, max_bytes=4)` | Step-by-step trace of the computation. |
| `export_c(config, function_name=None)` | Table-driven C99 source implementing `config`. |
| `build_table(config)` | The 256-entry lookup table (also used internally and by `export_c`). |
| `compute_bitwise(data, config)` | Canonical bit-by-bit reference implementation. |
| `compute_table(data, config, table=None)` | Fast table-driven implementation. |
| `self_test(config)` | Verifies a config against its `check` value. |
| `CRCConfig` | Dataclass: `name, width, poly, init, refin, refout, xorout, check`. |
| `CRC8_SMBUS`, `CRC16_CCITT_FALSE`, `CRC16_MODBUS`, `CRC32_ISO_HDLC` | Built-in preset configs. |

### `bitlab.parity`

| Function | Description |
|---|---|
| `get_parity_bit(value, type="even", bit_width=8)` | Computes the parity bit for `value`. |
| `append_parity(value, type="even", bit_width=8)` | Returns `value` with a parity bit appended as bit `bit_width`. |
| `check_parity(value_with_parity, type="even", bit_width=8)` | Returns `True` if the parity bit matches the data. |
| `generate_parity_array(values, type="even", bit_width=8)` | Parity bit for each value in a sequence. |
| `check_parity_array(values_with_parity, type="even", bit_width=8)` | Parity check for each value in a sequence. |
| `compute_message_parity(message, type="even")` | Single overall parity bit for a whole string. |
| `flip_random_bit(value, bit_width=8)` | Flips one random bit — useful for simulating errors in tests. |
| `encode_hamming(data)` | Encodes a 4-bit value (0–15) into a 7-bit Hamming codeword. |
| `decode_hamming(codeword)` | Decodes a 7-bit codeword, correcting a single-bit error if present. |

### `bitlab.bitutils`

| Function | Description |
|---|---|
| `popcount(n)` | Number of 1-bits. |
| `has_odd_parity(n)` | True if `n` has an odd number of 1-bits. |
| `get_bit` / `set_bit` / `flip_bit` | Single-bit read/write/toggle. |
| `reflect(value, width)` | Bit-mirror the lowest `width` bits. |
| `rotate_left` / `rotate_right` | Bitwise rotation within a fixed-width register. |

## Roadmap

Planned next:

- **Register field mapper** — define a hardware register's bit layout in
  Python, pack/unpack values, export to C `#define`s or a bitfield struct.
- **Computer architecture toolkit** — IEEE 754 float deconstruction,
  endianness swapping, Gray code, Q-format fixed-point conversion.
- **COBS framing** — Consistent Overhead Byte Stuffing for serial protocols.
- **Reed-Solomon** — burst error correction (QR codes, satellite comms) —
  planned as a later, dedicated release given its complexity.

## Development

```bash
pip install -e ".[dev]"
pytest              # run the test suite (56 tests, including compiling
                     # and running the generated C against gcc)
python -m build      # produce a wheel + sdist in dist/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full dev workflow and release
process, and [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT
