"""Step-by-step COBS encoding trace — the educational counterpart to
`cobs_encode()`.
"""

from __future__ import annotations

from typing import List, NamedTuple

_MAX_BLOCK = 0xFF


class _Block(NamedTuple):
    start: int
    end: int  # exclusive
    payload: bytes
    code: int
    reason: str


def _encode_with_trace(data: bytes) -> "tuple[bytes, List[_Block]]":
    """Runs the real COBS encode algorithm while recording each block's
    boundaries, so the trace can never drift from the actual output."""
    output = bytearray()
    output.append(0)
    code_index = 0
    code = 1
    block_start = 0
    blocks: List[_Block] = []

    for i, byte in enumerate(data):
        if byte == 0:
            output[code_index] = code
            blocks.append(_Block(block_start, i, data[block_start:i], code, "hit a zero byte"))
            code_index = len(output)
            output.append(0)
            code = 1
            block_start = i + 1
        else:
            output.append(byte)
            code += 1
            if code == _MAX_BLOCK:
                output[code_index] = code
                blocks.append(_Block(block_start, i + 1, data[block_start : i + 1], code, "reached the 254-byte block limit"))
                code_index = len(output)
                output.append(0)
                code = 1
                block_start = i + 1

    output[code_index] = code
    blocks.append(_Block(block_start, len(data), data[block_start:], code, "end of input"))

    return bytes(output), blocks


def explain_cobs(data: bytes, max_blocks: int = 6) -> str:
    """Traces through COBS-encoding `data` one block at a time.

    Args:
        data: The bytes to encode.
        max_blocks: Show detail for at most this many blocks, then
            summarize the rest (keeps the trace readable for long payloads).
    """
    encoded, blocks = _encode_with_trace(data)

    lines = [
        "COBS encode",
        f"Input ({len(data)} bytes): {data[:24].hex(' ')}" + (" ..." if len(data) > 24 else ""),
        "",
        "Rule: scan for the next zero byte (or 254 non-zero bytes, whichever",
        "comes first). Emit [count][the non-zero bytes], where count = distance",
        "to the next block (including the count byte itself). A zero byte is",
        "never emitted -- it's replaced by starting a new block.",
        "",
    ]

    for idx, block in enumerate(blocks):
        if idx >= max_blocks:
            lines.append(f"... ({len(blocks) - max_blocks} more blocks, same pattern) ...")
            break
        payload_hex = block.payload.hex(" ") if block.payload else "(empty)"
        lines.append(
            f"Block {idx}: bytes {block.start}-{max(block.start, block.end - 1)} = {payload_hex}  "
            f"({block.reason}) -> emit [0x{block.code:02X}] {payload_hex}"
        )

    lines.append("")
    lines.append(f"Encoded ({len(encoded)} bytes): {encoded[:24].hex(' ')}" + (" ..." if len(encoded) > 24 else ""))
    lines.append(f"Contains a zero byte: {'yes (BUG)' if 0 in encoded else 'no'}")
    lines.append("A single 0x00 can now be appended as an unambiguous frame delimiter.")

    return "\n".join(lines)
