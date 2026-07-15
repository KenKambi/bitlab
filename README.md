# bitlab

[![CI](https://github.com/KenKambi/bitlab/actions/workflows/ci.yml/badge.svg)](https://github.com/KenKambi/bitlab/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/bitlab.svg)](https://pypi.org/project/bitlab/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Design. Understand. Ship it.**

bitlab is a toolkit for embedded systems, binary data, and digital
communications — parity checking, Hamming error correction, CRC, and
hardware register bit-fields.


| Layer | What it's for |
|---|---|
| **Compute** | Fast, production-ready functions (`crc32()`, `pack()`, ...) |
| **Explain** | The same computation, narrated step by step — for learning or debugging |
| **Export** | Generate compiled-and-tested C source for the embedded target |


```bash
pip install bitlab
```

## See it in 20 seconds

Most CRC libraries give you a black box. `explain()` shows you the real
algorithm running, bit by bit:

```python
>>> from bitlab.crc import explain, CRC8_SMBUS
>>> print(explain(b"AB", CRC8_SMBUS))
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

And when you're ready for hardware, the same configuration exports straight
to a firmware-ready C function — no rewriting the algorithm by hand:

```python
>>> from bitlab.crc import export_c, CRC32_ISO_HDLC
>>> print(export_c(CRC32_ISO_HDLC, function_name="my_crc32"))
```
```c
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

The test suite compiles every
generated C function with `gcc` and checks the output against the official
CRC catalogue check values.

## Modules

```
bitlab/
├── bitutils/    foundational bit ops shared by every submodule
├── parity/      parity bit checking + Hamming(7,4) error correction
├── crc/         CRC-8/16/32, generic engine, explain(), export_c()
└── registers/   hardware register bit-field mapper, explain(), export_c()
```

### `bitlab.crc` — crc8/16/32, explain

Real hardware (Ethernet, Modbus, firmware integrity checks) uses CRC, not
simple parity. All four built-in presets are verified against the official
CRC-catalogue check values, not just "a CRC that happens to run."

```python
from bitlab.crc import crc8, crc16, crc32

crc8(b"hello")                       # CRC-8/SMBUS
crc16(b"hello")                      # CRC-16/CCITT-FALSE (default)
crc16(b"hello", variant="modbus")    # CRC-16/MODBUS
crc32(b"hello")                       # CRC-32/ISO-HDLC (Ethernet, zlib, PNG)
```

Custom polynomials work the same way:

```python
from bitlab.crc import crc, CRCConfig

my_crc = CRCConfig(
    name="my-custom-crc",
    width=16, poly=0x8005, init=0xFFFF,
    refin=True, refout=True, xorout=0x0000,
    check=0x4B37,  # CRC of b"123456789", used to self-test your config
)
crc(b"some data", my_crc)
```

### `bitlab.registers` — embedded, explaim
Firmware engineers hand-write register bitmasks constantly. Define the
layout once, pack/unpack named fields instead of shifting magic numbers by
hand, and export it straight to C.

```python
from bitlab.registers import Register, explain, export_c

reg = Register("UART_CR1", size_bits=8)
reg.add_field("ENABLE", bit_index=0)
reg.add_field("MODE", bit_range=(1, 3))
reg.add_field("TXIE", bit_index=7)

reg.pack(ENABLE=1, MODE=0b101, TXIE=1)   # -> 0x8B
reg.unpack(0x8B)                          # -> {'ENABLE': 1, 'MODE': 5, 'TXIE': 1}
```

```python
>>> print(explain(reg, ENABLE=1, MODE=5, TXIE=1))
Register: UART_CR1 (8-bit)

Bit:   7      6      5      4      3      2      1      0
Field: TXIE   .      .      .      MODE   MODE   MODE   ENABLE

Fields (MSB to LSB):
  TXIE         bit 7        (max 1)
  MODE         bits 1-3     (max 7)
  ENABLE       bit 0        (max 1)

Reserved (unassigned):
  bits 4-6

Packing UART_CR1(ENABLE=1, MODE=5, TXIE=1):
  ENABLE=1 -> 0b1 shifted left 0 -> 0x01  |  running value = 0x01
  MODE=5 -> 0b101 shifted left 1 -> 0x0A  |  running value = 0x0B
  TXIE=1 -> 0b1 shifted left 7 -> 0x80  |  running value = 0x8B

Final packed value: 0x8B (0b10001011)
```

`export_c(reg)` gives you portable `#define` position/mask macros with
`SET_`/`GET_` helpers (the recommended, compiler-independent style).
`export_c(reg, style="struct")` gives you a readable C bit-field struct
instead — with an explicit comment flagging that C leaves struct bit-field
ordering implementation-defined, so you know to double-check it against
your compiler before trusting exact hardware placement.

```c
#define UART_CR1_ENABLE_POS   0U
#define UART_CR1_ENABLE_MASK  (0x1U << UART_CR1_ENABLE_POS)

#define UART_CR1_SET_ENABLE(reg, val) \
    ((reg) = ((uint8_t)(reg) & ~UART_CR1_ENABLE_MASK) | \
    (((uint8_t)(val) << UART_CR1_ENABLE_POS) & UART_CR1_ENABLE_MASK))
#define UART_CR1_GET_ENABLE(reg) \
    (((uint8_t)(reg) & UART_CR1_ENABLE_MASK) >> UART_CR1_ENABLE_POS)
```

### `bitlab.parity` — parity bit, Hamming(7,4)

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
decode_hamming(corrupted)
# HammingDecodeResult(data=13, error_position=6, corrected=True, codeword=...)
```

### `bitlab.bitutils` — shared foundation

```python
from bitlab.bitutils import popcount, reflect, rotate_left, rotate_right

popcount(0b1011)                 # -> 3
reflect(0b1100, 4)               # -> 0b0011
rotate_left(0b10000001, 1, 8)     # -> 0b00000011
```

## CLI

One `bitlab` command covers every module:

```bash
bitlab crc explain "AB" --preset crc8
bitlab crc export-c --preset crc32 --name my_crc32

bitlab registers explain --name UART_CR1 --size 8 \
    --field ENABLE:0 --field MODE:1-3 --field TXIE:7 --pack ENABLE=1,MODE=5,TXIE=1
bitlab registers export-c --name UART_CR1 --size 8 \
    --field ENABLE:0 --field MODE:1-3 --field TXIE:7 --style defines

bitlab parity bit 0b1011 --type even --width 4
bitlab hamming encode 13
```

Run `bitlab --help`, `bitlab crc --help`, `bitlab registers --help` for full usage.

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
| `build_table(config)` | The 256-entry lookup table (also used by `export_c`). |
| `compute_bitwise(data, config)` | Canonical bit-by-bit reference implementation. |
| `compute_table(data, config, table=None)` | Fast table-driven implementation. |
| `self_test(config)` | Verifies a config against its `check` value. |
| `CRCConfig` | Dataclass: `name, width, poly, init, refin, refout, xorout, check`. |
| `CRC8_SMBUS`, `CRC16_CCITT_FALSE`, `CRC16_MODBUS`, `CRC32_ISO_HDLC` | Built-in preset configs. |

### `bitlab.registers`

| Function | Description |
|---|---|
| `Register(name, size_bits=8)` | Define a register. |
| `.add_field(name, bit_index=... \| bit_range=(start, end), description=None)` | Add a named field. Raises on overlap or out-of-bounds. |
| `.pack(**values)` | Pack named field values into a raw integer. |
| `.unpack(raw)` | Unpack a raw integer into `{field_name: value}`. |
| `.get_field(raw, name)` / `.set_field(raw, name, value)` | Read/modify a single field (read-modify-write). |
| `.reserved_ranges()` | Unassigned bit ranges. |
| `.layout()` | Fields ordered MSB to LSB. |
| `explain(reg, **values)` | Bit diagram, field list, and (if values given) a pack trace. |
| `export_c(reg, style="defines"\|"struct")` | C99 source: portable macros or a bit-field struct. |

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

- **v0.3.0 — Computer architecture toolkit** (`bitlab.arch`): IEEE 754
  float deconstruction, endianness swapping, Gray code, Q-format
  fixed-point conversion.
- **v0.4.0 — Protocol framing** (`bitlab.comms`): COBS (Consistent Overhead
  Byte Stuffing).
- **v1.0.0 — Reed-Solomon** (`bitlab.ecc`): burst error correction (QR
  codes, satellite comms) — planned as a dedicated release given its
  complexity.

See [CHANGELOG.md](CHANGELOG.md) for full release history.

## Development

```bash
pip install -e ".[dev]"
pytest              # 77 tests, including compiling and running generated
                     # C against gcc for both crc and registers
python -m build      # produce a wheel + sdist in dist/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full dev workflow and release
process.

## License

MIT
