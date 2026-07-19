"""GF(256) (Galois Field of 256 elements) arithmetic.

Reed-Solomon over bytes works in GF(256): the 256 possible byte values,
with addition/subtraction being XOR and multiplication/division defined via
a primitive polynomial. Every value in bitlab uses the same field
parameters as the classic RS(255, k) codes used in QR codes, CDs, DVDs,
and CCSDS deep-space telemetry:

    primitive polynomial: x^8 + x^4 + x^3 + x^2 + 1  (0x11D)
    generator element: 2

These exact parameters (and this module's tables) were cross-validated
against the independent `reedsolo` library across tens of thousands of
field operations during development -- see the test suite.
"""

from __future__ import annotations

from typing import List, Tuple

PRIM = 0x11D
GENERATOR = 2


def _build_tables(prim: int = PRIM) -> Tuple[List[int], List[int]]:
    exp = [0] * 512
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= prim
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log


_EXP, _LOG = _build_tables()


def gf_mul(x: int, y: int) -> int:
    """Multiplies two GF(256) elements."""
    if x == 0 or y == 0:
        return 0
    return _EXP[_LOG[x] + _LOG[y]]


def gf_div(x: int, y: int) -> int:
    """Divides two GF(256) elements. Raises ZeroDivisionError if y == 0."""
    if y == 0:
        raise ZeroDivisionError("gf_div: division by zero")
    if x == 0:
        return 0
    return _EXP[(_LOG[x] - _LOG[y]) % 255]


def gf_pow(x: int, power: int) -> int:
    """Raises a GF(256) element to an (possibly negative) integer power."""
    if x == 0:
        return 0
    return _EXP[(_LOG[x] * power) % 255]


def gf_inverse(x: int) -> int:
    """Returns the multiplicative inverse of a nonzero GF(256) element."""
    return _EXP[255 - _LOG[x]]
