"""COBS (Consistent Overhead Byte Stuffing).

Removes all zero bytes from a payload by replacing runs of non-zero bytes
with a length-prefixed block, so a single zero byte can be used as an
unambiguous packet delimiter on a serial link (UART, SPI-over-wire framing,
etc.) — the receiver can always find the start of the next packet even after
a corrupted/desynced byte stream, which plain length-prefixing can't do.

Overhead is at most 1 byte per 254 bytes of payload, plus 1 byte fixed
overhead — the "consistent" in the name.

Reference: Cheshire & Baker, "Consistent Overhead Byte Stuffing" (IEEE/ACM
Transactions on Networking, 1999).
"""

from __future__ import annotations

_MAX_BLOCK = 0xFF


def cobs_encode(data: bytes) -> bytes:
    """COBS-encodes `data`. The result never contains a zero byte, so it's
    safe to append/prepend 0x00 as a frame delimiter around it.
    """
    output = bytearray()
    output.append(0)  # placeholder for the first block's length byte
    code_index = 0
    code = 1

    for byte in data:
        if byte == 0:
            output[code_index] = code
            code_index = len(output)
            output.append(0)  # placeholder
            code = 1
        else:
            output.append(byte)
            code += 1
            if code == _MAX_BLOCK:
                output[code_index] = code
                code_index = len(output)
                output.append(0)  # placeholder
                code = 1

    output[code_index] = code
    return bytes(output)


def cobs_decode(encoded: bytes) -> bytes:
    """Reverses `cobs_encode`. Raises ValueError if `encoded` is malformed
    (contains an embedded zero byte where a length byte was expected, or is
    truncated mid-block).
    """
    output = bytearray()
    i = 0
    n = len(encoded)

    while i < n:
        code = encoded[i]
        if code == 0:
            raise ValueError(f"unexpected zero byte at position {i} (COBS length bytes are never 0)")
        i += 1

        remaining = code - 1
        if i + remaining > n:
            raise ValueError(
                f"truncated COBS data: block at position {i - 1} claims {remaining} "
                f"following bytes but only {n - i} remain"
            )
        block = encoded[i : i + remaining]
        if 0 in block:
            raise ValueError(
                f"zero byte found inside a data block at position {i + block.index(0)} "
                f"(a valid COBS block never contains a zero byte -- this indicates corrupted input)"
            )
        output.extend(block)
        i += remaining

        if code < _MAX_BLOCK and i < n:
            output.append(0)

    return bytes(output)


def cobs_frame(data: bytes) -> bytes:
    """Encodes `data` and appends the 0x00 delimiter, ready to write
    directly to a serial link."""
    return cobs_encode(data) + b"\x00"


def cobs_unframe(framed: bytes) -> bytes:
    """Strips a single trailing 0x00 delimiter (if present) and decodes.
    Convenience wrapper around `cobs_decode` for data read straight off a
    serial link."""
    if framed.endswith(b"\x00"):
        framed = framed[:-1]
    return cobs_decode(framed)
