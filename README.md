# bitlab

[![PyPI](https://img.shields.io/pypi/v/bitlab.svg)](https://pypi.org/project/bitlab/)
[![CI](https://github.com/KenKambi/bitlab/actions/workflows/ci.yml/badge.svg)](https://github.com/KenKambi/bitlab/actions/workflows/ci.yml)
[![Downloads](https://img.shields.io/pepy/dt/bitlab)](https://pepy.tech/projects/bitlab)
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
 ├── registers/   hardware register bit-field mapper, explain(), export_c()
 ├── arch/        IEEE 754, endianness, Gray code, Q-format fixed-point
 └── comms/       COBS framing, explain_cobs(), export_c()
```
### `bitlab.bitutils` — shared foundation

```python
from bitlab.bitutils import popcount, reflect, rotate_left, rotate_right

popcount(0b1011)                 # -> 3
reflect(0b1100, 4)               # -> 0b0011
rotate_left(0b10000001, 1, 8)     # -> 0b00000011
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

### `bitlab.registers` — embedded, explain
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
### `bitlab.arch` — computer architecture toolkit

IEEE 754 float deconstruction, endianness conversion, Gray code, and
Q-format fixed-point.

```python
from bitlab.arch import decompose

c = decompose(0.15625)
c.sign, c.exponent, c.classification   # -> (0, -3, 'normal')
hex(c.bits)                             # -> '0x3e200000'
```

The decomposition is built on Python's `struct` module — the platform's
actual IEEE 754 implementation — rather than reimplemented bit math, so
zero, subnormals, infinities, and NaN all decompose correctly without
special-casing.

```python
from bitlab.arch import swap_endianness

hex(swap_endianness(0x12345678, 4))   # -> '0x78563412'
```

```python
from bitlab.arch import binary_to_gray, gray_to_binary

bin(binary_to_gray(0b1011))    # -> '0b1110'
bin(gray_to_binary(0b1110))    # -> '0b1011'
```

```python
from bitlab.arch import float_to_q, q_to_float

raw = float_to_q(0.5, "Q1.15")   # -> 16384 (0x4000)
q_to_float(raw, "Q1.15")          # -> 0.5
```

Every topic has an `explain_*` function for a step-by-step trace, and the
two with genuine embedded-C payoff like byte swapping and Q-format conversion
export to C:

```python
from bitlab.arch import export_c_endian_swap, export_c_fixed_point

print(export_c_endian_swap(4, function_name="my_swap32"))
print(export_c_fixed_point("Q1.15"))
```

```c
static inline uint32_t my_swap32(uint32_t value)
{
    return ((value & 0x000000FFU) << 24) |
           ((value & 0x0000FF00U) << 8) |
           ((value & 0x00FF0000U) >> 8) |
           ((value & 0xFF000000U) >> 24);
}
```

IEEE 754 and Gray code intentionally don't export to C: C already gives you
bit-exact float access via a union or `memcpy`, and Gray code is a one-line
`n ^ (n >> 1)` that doesn't benefit from generated boilerplate. C export is
added where it replaces code people actually reimplement — not everywhere,
for the sake of a consistent feature checklist.

### `bitlab.comms` — COBS framing

Before sending data over UART or SPI, a receiver needs an unambiguous way
to find where one packet ends and the next begins. COBS (Consistent
Overhead Byte Stuffing) removes every zero byte from a payload, so a
single `0x00` can be used as a frame delimiter — with at most 1 byte of
overhead per 254 bytes of payload. (Note: `cobs-encode`/`cobs-decode` take hex strings as input, e.g. `11220033`, not raw text.)

```python
from bitlab.comms import cobs_encode, cobs_decode

encoded = cobs_encode(b"hello\x00world")
0x00 in encoded          # -> False, safe to use 0x00 as a delimiter
cobs_decode(encoded)     # -> b'hello\x00world'
```

`cobs_frame`/`cobs_unframe` add/strip the trailing delimiter for you, for
data going straight to/from a serial link:

```python
from bitlab.comms import cobs_frame, cobs_unframe

wire_bytes = cobs_frame(b"hello\x00world")   # ready to write to a UART
cobs_unframe(wire_bytes)                      # -> b'hello\x00world'
```

`cobs_decode` doesn't just trust its input — it rejects a truncated final
block and a zero byte in a position where a valid encoder would never put
one, which is a cheap way to catch line-noise corruption instead of
silently returning garbage.

```python
>>> from bitlab.comms import explain_cobs
>>> print(explain_cobs(bytes([0x11, 0x22, 0x00, 0x33])))
COBS encode
Input (4 bytes): 11 22 00 33

Rule: scan for the next zero byte (or 254 non-zero bytes, whichever
comes first). Emit [count][the non-zero bytes], where count = distance
to the next block (including the count byte itself). A zero byte is
never emitted -- it's replaced by starting a new block.

Block 0: bytes 0-1 = 11 22  (hit a zero byte) -> emit [0x03] 11 22
Block 1: bytes 3-3 = 33  (end of input) -> emit [0x02] 33

Encoded (5 bytes): 03 11 22 02 33
Contains a zero byte: no
A single 0x00 can now be appended as an unambiguous frame delimiter.
```

```python
from bitlab.comms import export_c

print(export_c())
```

```c
size_t cobs_encode(const uint8_t *src, size_t len, uint8_t *dst)
{
    size_t write_index = 1;
    size_t code_index = 0;
    uint8_t code = 1;
    /* ... */
}
```

Unlike `crc`/`registers`, there's no per-config table to generate for
COBS — it's a fixed algorithm, so `export_c()` emits a single well-tested
reference implementation rather than something parameterized. It's
validated the same way as everything else here: compiled with `gcc` and
property-tested against the Python implementation across thousands of
randomized inputs.

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

bitlab arch float 0.15625
bitlab arch endian 0x12345678 --width-bytes 4
bitlab arch gray-encode 0b1011
bitlab arch q-encode 0.5 --format Q1.15
bitlab comms cobs-encode 112200 33
bitlab comms cobs-explain 11220033
bitlab comms export-c
```
Run bitlab --help, bitlab crc --help, bitlab registers --help, bitlab arch --help, bitlab comms --help for full usage.

```
## API reference

### `bitlab.bitutils`

| Function | Description |
|---|---|
| `popcount(n)` | Number of 1-bits. |
| `has_odd_parity(n)` | True if `n` has an odd number of 1-bits. |
| `get_bit` / `set_bit` / `flip_bit` | Single-bit read/write/toggle. |
| `reflect(value, width)` | Bit-mirror the lowest `width` bits. |
| `rotate_left` / `rotate_right` | Bitwise rotation within a fixed-width register. |

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

### `bitlab.arch`

| Function | Description |
|---|---|
| `decompose(value, width=32\|64)` | Breaks a float into sign/exponent/mantissa fields (`IEEE754Components`). |
| `compose(sign, exponent_raw, mantissa, width=32\|64)` | Rebuilds a float from raw fields. |
| `to_bits(value, width)` / `from_bits(bits, width)` | Raw IEEE 754 bit pattern <-> float. |
| `explain_float(value, width=32)` | Step-by-step decomposition trace. |
| `swap_endianness(value, width_bytes)` | Reverses byte order of an unsigned integer. |
| `to_big_endian` / `to_little_endian` / `to_bytes` / `from_bytes` | Byte-order encode/decode helpers. |
| `explain_endianness(value, width_bytes)` | Byte-by-byte swap trace. |
| `export_c_endian_swap(width_bytes, function_name=None)` | C99 byte-swap function (2/4/8 bytes). |
| `binary_to_gray(n)` / `gray_to_binary(g)` | Binary <-> Gray code. |
| `explain_gray(n, width=8)` | Bit-by-bit Gray code trace. |
| `float_to_q(value, q_format="Q8.8", saturate=False)` | Float -> Q-format fixed-point integer. |
| `q_to_float(raw, q_format="Q8.8")` | Q-format fixed-point integer -> float. |
| `q_range(q_format)` | The representable `(min, max)` float range for a Q-format. |
| `parse_q_format(q_format)` | Parses `"Qm.n"` into `(integer_bits, fractional_bits)`. |
| `explain_fixed_point(value, q_format)` | Step-by-step fixed-point conversion trace. |
| `export_c_fixed_point(q_format, prefix=None)` | C99 macros for float <-> Q-format conversion. |

### `bitlab.comms`

| Function | Description |
|---|---|
| `cobs_encode(data)` | COBS-encodes `data`. Output never contains a zero byte. |
| `cobs_decode(encoded)` | Reverses `cobs_encode`. Raises `ValueError` on malformed input. |
| `cobs_frame(data)` / `cobs_unframe(framed)` | Encode+append, or strip+decode, the `0x00` delimiter. |
| `explain_cobs(data, max_blocks=6)` | Step-by-step block-by-block encode trace. |
| `export_c(encode_fn_name=..., decode_fn_name=...)` | Standalone C99 encode/decode functions. |
```
## Roadmap

- **v1.0.0 — Reed-Solomon** (`bitlab.ecc`): burst error correction (QR
  codes, satellite comms) — planned as a dedicated release given its
  complexity.
See [CHANGELOG.md](CHANGELOG.md) for full release history.

## Development

```bash
pip install -e ".[dev]"
pytest              # 150 tests, including compiling and running generated
                     # C against gcc for crc, registers, arch and comms
python -m build      # produce a wheel + sdist in dist/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full dev workflow and release
process.

## License

MIT
