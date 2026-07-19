"""Reed-Solomon encoding and syndrome-based decoding over GF(256).

Encodes a message by appending `nsym` parity symbols computed from a
generator polynomial (systematic encoding, so the original message bytes
appear unchanged at the start of the output). Decoding computes syndromes,
finds the error locator polynomial via Berlekamp-Massey, locates errors via
a Chien search, and computes error magnitudes via the Forney algorithm --
correcting up to `nsym // 2` symbol errors anywhere in the block, without
needing to know where they are in advance.

Operates on blocks of at most 255 bytes total (message + parity) -- the
fundamental limit of GF(256)-based Reed-Solomon. Splitting longer data into
multiple blocks is left to the caller (a natural fit for e.g. one block per
packet), since chunking strategy is genuinely application-specific.

This implementation was cross-validated during development against the
independent `reedsolo` library: byte-for-byte identical encode output, and
identical decode success/failure and recovered data across thousands of
randomized error-injection trials (see the test suite).
"""

from __future__ import annotations

from typing import List

from .gf256 import gf_div, gf_inverse, gf_mul, gf_pow
from .polynomial import poly_add, poly_div, poly_eval, poly_mul, poly_scale

MAX_BLOCK_SIZE = 255


class ReedSolomonError(Exception):
    """Raised when a Reed-Solomon codeword cannot be decoded (too many
    errors for the given number of parity symbols to correct)."""


def generator_poly(nsym: int) -> List[int]:
    """Builds the degree-`nsym` generator polynomial used for encoding:
    the product of (x - 2^i) for i in range(nsym)."""
    g = [1]
    for i in range(nsym):
        g = poly_mul(g, [1, gf_pow(2, i)])
    return g


def rs_encode(data: bytes, nsym: int) -> bytes:
    """Encodes `data`, returning `data` followed by `nsym` parity bytes.

    Args:
        data: The message bytes to protect. Must be non-empty.
        nsym: Number of parity symbols to add. Corrects up to `nsym // 2`
            byte errors anywhere in the resulting `len(data) + nsym` block.

    Raises:
        ValueError: if `data` is empty, `nsym` is not positive, or
            `len(data) + nsym` exceeds the 255-byte GF(256) block limit.
    """
    if len(data) == 0:
        raise ValueError("rs_encode: data must be non-empty")
    if nsym < 1:
        raise ValueError("rs_encode: nsym must be at least 1")
    if len(data) + nsym > MAX_BLOCK_SIZE:
        raise ValueError(
            f"rs_encode: len(data) ({len(data)}) + nsym ({nsym}) = "
            f"{len(data) + nsym} exceeds the GF(256) block limit of {MAX_BLOCK_SIZE}"
        )

    gen = generator_poly(nsym)
    msg = list(data) + [0] * nsym
    for i in range(len(data)):
        coef = msg[i]
        if coef != 0:
            for j in range(1, len(gen)):
                msg[i + j] ^= gf_mul(gen[j], coef)
    return bytes(list(data) + msg[len(data):])


def rs_calc_syndromes(msg: List[int], nsym: int) -> List[int]:
    """Computes the syndrome polynomial for `msg` (a leading 0 is
    prepended, following the standard convention; downstream steps account
    for it)."""
    return [0] + [poly_eval(msg, gf_pow(2, i)) for i in range(nsym)]


def _find_error_locator(synd: List[int], nsym: int) -> List[int]:
    """Berlekamp-Massey algorithm: finds the error locator polynomial."""
    err_loc = [1]
    old_loc = [1]
    synd_shift = len(synd) - nsym
    for i in range(nsym):
        K = i + synd_shift
        delta = synd[K]
        for j in range(1, len(err_loc)):
            delta ^= gf_mul(err_loc[-(j + 1)], synd[K - j])
        old_loc = old_loc + [0]
        if delta != 0:
            if len(old_loc) > len(err_loc):
                new_loc = poly_scale(old_loc, delta)
                old_loc = poly_scale(err_loc, gf_inverse(delta))
                err_loc = new_loc
            err_loc = poly_add(err_loc, poly_scale(old_loc, delta))

    i = 0
    while i < len(err_loc) - 1 and err_loc[i] == 0:
        i += 1
    err_loc = err_loc[i:]
    errs = len(err_loc) - 1
    if errs * 2 > nsym:
        raise ReedSolomonError("Too many errors to correct")
    return err_loc


def _find_errors(err_loc: List[int], nmess: int) -> List[int]:
    """Chien search: finds the roots of the error locator polynomial,
    i.e. the byte positions where errors occurred."""
    errs = len(err_loc) - 1
    err_pos = []
    for i in range(nmess):
        if poly_eval(err_loc, gf_pow(2, i)) == 0:
            err_pos.append(nmess - 1 - i)
    if len(err_pos) != errs:
        raise ReedSolomonError("Chien search found the wrong number of error positions")
    return err_pos


def _find_error_evaluator(synd: List[int], err_loc: List[int], nsym: int) -> List[int]:
    product = poly_mul(synd, err_loc)
    divisor = [1] + [0] * (nsym + 1)
    _, remainder = poly_div(product, divisor)
    return remainder


def _correct_errata(msg: List[int], synd: List[int], err_pos: List[int]) -> List[int]:
    """Forney algorithm: computes and applies the error magnitudes."""
    coef_pos = [len(msg) - 1 - p for p in err_pos]
    err_loc = [1]
    for cp in coef_pos:
        err_loc = poly_mul(err_loc, poly_add([1], [gf_pow(2, cp), 0]))
    err_eval = _find_error_evaluator(synd[::-1], err_loc, len(err_loc) - 1)[::-1]

    locations = [gf_pow(2, -((255 - cp) % 255)) for cp in coef_pos]

    magnitudes = [0] * len(msg)
    for i, Xi in enumerate(locations):
        Xi_inv = gf_inverse(Xi)
        err_loc_prime = 1
        for j, Xj in enumerate(locations):
            if j != i:
                err_loc_prime = gf_mul(err_loc_prime, 1 ^ gf_mul(Xi_inv, Xj))
        if err_loc_prime == 0:
            raise ReedSolomonError("Forney algorithm failed to locate an error")
        y = poly_eval(err_eval[::-1], Xi_inv)
        y = gf_mul(Xi, y)
        magnitudes[err_pos[i]] = gf_div(y, err_loc_prime)

    return [m ^ e for m, e in zip(msg, magnitudes)]


def rs_decode(data: bytes, nsym: int) -> bytes:
    """Decodes a Reed-Solomon-encoded block, correcting up to `nsym // 2`
    byte errors, and returns the original message (without parity bytes).

    Raises:
        ReedSolomonError: if there are too many errors to correct. This is
            detected in the vast majority of over-capacity cases (verified
            empirically during development), but -- as with any RS code --
            isn't a mathematical guarantee for every possible corruption
            pattern beyond the correction capacity.
        ValueError: if `data` is not longer than `nsym`.
    """
    if len(data) <= nsym:
        raise ValueError("rs_decode: data must be longer than nsym")

    msg = list(data)
    synd = rs_calc_syndromes(msg, nsym)
    if max(synd) == 0:
        return bytes(msg[:-nsym])

    err_loc = _find_error_locator(synd, nsym)
    err_pos = _find_errors(err_loc[::-1], len(msg))
    corrected = _correct_errata(msg, synd, err_pos)

    verify = rs_calc_syndromes(corrected, nsym)
    if max(verify) != 0:
        raise ReedSolomonError("Decoding failed: could not fully correct the message")

    return bytes(corrected[:-nsym])
