"""Polynomial arithmetic over GF(256).

Polynomials are represented as lists of coefficients, highest-degree term
first -- e.g. `1 + 2x + 5x^2` is `[5, 2, 1]`. This matches the convention
used throughout the classic Reed-Solomon literature and makes Horner's-
method evaluation (`poly_eval`) read naturally.
"""

from __future__ import annotations

from typing import List, Tuple

from .gf256 import gf_mul


def poly_scale(p: List[int], x: int) -> List[int]:
    """Multiplies every coefficient of `p` by the scalar `x`."""
    return [gf_mul(c, x) for c in p]


def poly_add(p: List[int], q: List[int]) -> List[int]:
    """Adds two polynomials (XOR of aligned coefficients)."""
    if len(p) < len(q):
        p, q = q, p
    r = list(p)
    offset = len(p) - len(q)
    for i in range(len(q)):
        r[i + offset] ^= q[i]
    return r


def poly_mul(p: List[int], q: List[int]) -> List[int]:
    """Multiplies two polynomials."""
    r = [0] * (len(p) + len(q) - 1)
    for i, pc in enumerate(p):
        if pc == 0:
            continue
        for j, qc in enumerate(q):
            r[i + j] ^= gf_mul(pc, qc)
    return r


def poly_eval(p: List[int], x: int) -> int:
    """Evaluates `p` at `x` using Horner's method."""
    y = p[0]
    for c in p[1:]:
        y = gf_mul(y, x) ^ c
    return y


def poly_div(dividend: List[int], divisor: List[int]) -> Tuple[List[int], List[int]]:
    """Divides `dividend` by `divisor` via synthetic division.

    Returns (quotient, remainder). Note: this expects the same
    highest-degree-first coefficient order as the rest of this module.
    """
    msg_out = list(dividend)
    for i in range(len(dividend) - (len(divisor) - 1)):
        coef = msg_out[i]
        if coef != 0:
            for j in range(1, len(divisor)):
                if divisor[j] != 0:
                    msg_out[i + j] ^= gf_mul(divisor[j], coef)
    separator = -(len(divisor) - 1)
    return msg_out[:separator], msg_out[separator:]
