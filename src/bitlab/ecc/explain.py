"""Step-by-step Reed-Solomon encoding trace -- the educational counterpart
to `rs_encode()`.

Decoding (syndromes, Berlekamp-Massey, Chien search, Forney) doesn't get an
`explain()`: a faithful trace would run to hundreds of lines for even a
tiny example and wouldn't actually help anyone understand the algorithm
better than a good diagram would. Encoding is where a step-by-step trace
earns its keep -- it's short, and it directly shows *why* the parity bytes
are what they are.
"""

from __future__ import annotations

from .gf256 import gf_mul, gf_pow
from .reed_solomon import generator_poly


def explain_rs_encode(data: bytes, nsym: int) -> str:
    """Traces through RS-encoding `data` with `nsym` parity symbols."""
    if len(data) == 0:
        raise ValueError("explain_rs_encode: data must be non-empty")
    if len(data) + nsym > 255:
        raise ValueError("explain_rs_encode: len(data) + nsym exceeds the 255-byte block limit")

    lines = []
    lines.append("Reed-Solomon encode")
    lines.append(f"Message ({len(data)} bytes): {data.hex(' ')}")
    lines.append(f"Parity symbols requested: {nsym}  (corrects up to {nsym // 2} byte errors)")
    lines.append("")

    gen = generator_poly(nsym)
    lines.append(f"Generator polynomial g(x) = product of (x - 2^i) for i in 0..{nsym - 1}:")
    lines.append(f"  roots at 2^0..2^{nsym - 1} = " + ", ".join(str(gf_pow(2, i)) for i in range(nsym)))
    lines.append(f"  g(x) coefficients (highest degree first): {gen}")
    lines.append("")

    lines.append("Systematic encoding: append nsym zero bytes to the message, then repeatedly")
    lines.append("XOR a scaled copy of g(x) into the tail to cancel each message byte in turn")
    lines.append("(this is polynomial long division -- the parity is message(x)*x^nsym mod g(x)):")
    lines.append("")

    msg = list(data) + [0] * nsym
    for i in range(len(data)):
        coef = msg[i]
        before = list(msg)
        if coef != 0:
            for j in range(1, len(gen)):
                msg[i + j] ^= gf_mul(gen[j], coef)
        lines.append(f"  byte {i} = 0x{data[i]:02X}: tail before {before[i:]} -> tail after {msg[i:]}")

    parity = msg[len(data):]
    lines.append("")
    lines.append(f"Parity bytes: {bytes(parity).hex(' ')}")
    lines.append(f"Encoded output ({len(data) + nsym} bytes): {(data + bytes(parity)).hex(' ')}")

    return "\n".join(lines)
