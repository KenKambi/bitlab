"""Human-readable, step-by-step CRC trace — the educational counterpart to
the fast `compute()` path.

`explain()` runs the exact same bitwise algorithm as `engine.compute_bitwise`
(this is not a separate/approximate explanation — it's the real computation
with a narration attached), so what a student reads here is guaranteed to
match what the fast path actually computes.
"""

from __future__ import annotations

from ..bitutils import reflect
from .presets import CRCConfig


def explain(data: bytes, config: CRCConfig, max_bytes: int = 4) -> str:
    """Returns a step-by-step trace of computing the CRC of `data` under
    `config`.

    Args:
        data: The bytes to checksum.
        config: The CRC configuration to explain.
        max_bytes: Show detailed per-byte register state for at most this
            many leading bytes, then summarize the rest (keeps the trace
            readable for longer payloads).
    """
    width = config.width
    mask = (1 << width) - 1
    topbit = 1 << (width - 1)
    hexw = width // 4
    reg = config.init & mask

    lines = []
    lines.append(f"CRC algorithm: {config.name}")
    lines.append(
        f"  width={width}  poly=0x{config.poly:0{hexw}X}  init=0x{config.init:0{hexw}X}  "
        f"refin={config.refin}  refout={config.refout}  xorout=0x{config.xorout:0{hexw}X}"
    )
    lines.append("")
    lines.append(f"Input bytes ({len(data)} total): {data[:16].hex(' ')}" + (" ..." if len(data) > 16 else ""))
    lines.append("")
    lines.append(f"Initial register: 0x{reg:0{hexw}X}")

    for i, byte in enumerate(data):
        b = reflect(byte, 8) if config.refin else byte
        reg ^= (b << (width - 8)) & mask

        if i < max_bytes:
            note = " (bit-reversed for refin)" if config.refin else ""
            lines.append("")
            lines.append(f"Byte {i}: 0x{byte:02X}{note} -> XORed in, register = 0x{reg:0{hexw}X}")

        for bit_num in range(8):
            if reg & topbit:
                reg = ((reg << 1) ^ config.poly) & mask
                bit_note = "MSB=1 -> shift left, XOR polynomial"
            else:
                reg = (reg << 1) & mask
                bit_note = "MSB=0 -> shift left"
            if i < max_bytes:
                lines.append(f"    bit {bit_num}: {bit_note} -> 0x{reg:0{hexw}X}")

        if i == max_bytes and len(data) > max_bytes:
            lines.append("")
            lines.append(f"... ({len(data) - max_bytes} more bytes processed the same way) ...")

    lines.append("")
    lines.append(f"Register after all bytes: 0x{reg:0{hexw}X}")

    if config.refout:
        reg = reflect(reg, width)
        lines.append(f"refout=True -> bit-reverse register: 0x{reg:0{hexw}X}")

    result = (reg ^ config.xorout) & mask
    lines.append(f"XOR with xorout (0x{config.xorout:0{hexw}X}): 0x{result:0{hexw}X}")
    lines.append("")
    lines.append(f"Final CRC: 0x{result:0{hexw}X}")

    return "\n".join(lines)
