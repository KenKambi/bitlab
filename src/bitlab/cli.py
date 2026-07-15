"""Unified command-line interface for bitlab.

Usage:
    bitlab parity bit <value> [--type even|odd] [--width N]
    bitlab parity append <value> [--type even|odd] [--width N]
    bitlab parity check <value> [--type even|odd] [--width N]

    bitlab hamming encode <4bitValue>
    bitlab hamming decode <7bitCodeword>

    bitlab crc compute <data> [--preset crc8|crc16-ccitt|crc16-modbus|crc32] [--hex]
    bitlab crc explain <data> [--preset ...] [--hex]
    bitlab crc export-c [--preset ...] [--name FN_NAME]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict

from .crc.engine import compute
from .crc.codegen import export_c as crc_export_c
from .crc.explain import explain as crc_explain
from .crc.presets import PRESETS
from .parity.hamming import decode_hamming, encode_hamming
from .parity.parity import ParityType, append_parity, check_parity, get_parity_bit
from .registers.codegen import export_c as reg_export_c
from .registers.core import Register
from .registers.explain import explain as reg_explain


def _parse_number(token: str) -> int:
    """Parses a decimal, 0b-binary, or 0x-hex integer literal."""
    return int(token, 0) if token.lower().startswith(("0b", "0x", "0o")) else int(token)


def _parse_crc_data(value: str, as_hex: bool) -> bytes:
    if as_hex:
        cleaned = value.replace(" ", "").replace("0x", "")
        return bytes.fromhex(cleaned)
    return value.encode("utf-8")


def _build_register(name: str, size: int, field_specs: "list[str]") -> Register:
    reg = Register(name, size_bits=size)
    for spec in field_specs:
        if ":" not in spec:
            raise SystemExit(f"Invalid --field {spec!r}, expected NAME:BIT or NAME:START-END")
        fname, bits = spec.split(":", 1)
        if "-" in bits:
            start_str, end_str = bits.split("-", 1)
            reg.add_field(fname, bit_range=(int(start_str), int(end_str)))
        else:
            reg.add_field(fname, bit_index=int(bits))
    return reg


def _parse_pack_values(spec: str) -> "dict[str, int]":
    values = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise SystemExit(f"Invalid --pack entry {part!r}, expected NAME=VALUE")
        name, val = part.split("=", 1)
        values[name.strip()] = _parse_number(val.strip())
    return values


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bitlab",
        description="Toolkit for parity, Hamming codes, and CRC — computation, "
        "explanation, and C code export.",
    )
    subparsers = parser.add_subparsers(dest="group")

    # --- parity ---
    parity_parser = subparsers.add_parser("parity", help="Parity bit tools")
    parity_sub = parity_parser.add_subparsers(dest="command")

    def add_parity_args(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("value", type=str, help="Integer value (decimal, 0b, or 0x)")
        sub.add_argument("--type", choices=["even", "odd"], default="even")
        sub.add_argument("--width", type=int, default=8)

    add_parity_args(parity_sub.add_parser("bit", help="Print the parity bit for a value"))
    add_parity_args(parity_sub.add_parser("append", help="Append a parity bit to a value"))
    add_parity_args(
        parity_sub.add_parser("check", help="Check parity of a value with parity bit appended")
    )

    # --- hamming ---
    hamming_parser = subparsers.add_parser("hamming", help="Hamming(7,4) error correction")
    hamming_sub = hamming_parser.add_subparsers(dest="command")
    encode_p = hamming_sub.add_parser("encode", help="Encode a 4-bit value into a 7-bit codeword")
    encode_p.add_argument("value", type=str)
    decode_p = hamming_sub.add_parser("decode", help="Decode/correct a 7-bit codeword")
    decode_p.add_argument("value", type=str)

    # --- crc ---
    crc_parser = subparsers.add_parser("crc", help="CRC compute / explain / export-c")
    crc_sub = crc_parser.add_subparsers(dest="command")

    compute_p = crc_sub.add_parser("compute", help="Compute a CRC")
    compute_p.add_argument("data", type=str, help="Input data (UTF-8 text, or hex with --hex)")
    compute_p.add_argument("--preset", choices=list(PRESETS), default="crc32")
    compute_p.add_argument("--hex", action="store_true", help="Treat <data> as hex bytes")

    explain_p = crc_sub.add_parser("explain", help="Step-by-step CRC trace")
    explain_p.add_argument("data", type=str)
    explain_p.add_argument("--preset", choices=list(PRESETS), default="crc32")
    explain_p.add_argument("--hex", action="store_true")
    explain_p.add_argument("--max-bytes", type=int, default=4)

    export_p = crc_sub.add_parser("export-c", help="Export a CRC config as C source")
    export_p.add_argument("--preset", choices=list(PRESETS), default="crc32")
    export_p.add_argument("--name", type=str, default=None, help="C function name")

    # --- registers ---
    reg_parser = subparsers.add_parser("registers", help="Register bit-field mapper")
    reg_sub = reg_parser.add_subparsers(dest="command")

    def add_register_definition_args(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--name", type=str, required=True, help="Register name")
        sub.add_argument("--size", type=int, default=8, help="Register width in bits (default 8)")
        sub.add_argument(
            "--field",
            action="append",
            required=True,
            metavar="NAME:BIT",
            help="Add a field. NAME:5 for a single bit, NAME:1-3 for a bit range. "
            "Repeat --field for each field.",
        )

    reg_explain_p = reg_sub.add_parser("explain", help="Show a register's bit layout")
    add_register_definition_args(reg_explain_p)
    reg_explain_p.add_argument(
        "--pack", type=str, default=None, metavar="NAME=VAL,...",
        help="Also trace packing these field values, e.g. ENABLE=1,MODE=5",
    )

    reg_export_p = reg_sub.add_parser("export-c", help="Export a register as C source")
    add_register_definition_args(reg_export_p)
    reg_export_p.add_argument("--style", choices=["defines", "struct"], default="defines")

    return parser


def main(argv: "list[str] | None" = None) -> int:
    try:
        return _main(argv)
    except BrokenPipeError:
        # Output was piped into something like `head` that closed early.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0


def _main(argv: "list[str] | None") -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.group is None or getattr(args, "command", None) is None:
        parser.print_help()
        return 0 if args.group is None else 1

    if args.group == "parity":
        value = _parse_number(args.value)
        type_: ParityType = args.type
        width: int = args.width
        if args.command == "bit":
            print(get_parity_bit(value, type_, width))
        elif args.command == "append":
            result = append_parity(value, type_, width)
            print(f"{result} (0b{result:b})")
        elif args.command == "check":
            print(check_parity(value, type_, width))
        return 0

    if args.group == "hamming":
        value = _parse_number(args.value)
        if args.command == "encode":
            codeword = encode_hamming(value)
            print(f"{codeword} (0b{codeword:07b})")
        elif args.command == "decode":
            result = decode_hamming(value)
            print(json.dumps(asdict(result), indent=2))
        return 0

    if args.group == "crc":
        config = PRESETS[args.preset]
        if args.command == "compute":
            data = _parse_crc_data(args.data, args.hex)
            result = compute(data, config)
            hexw = config.width // 4
            print(f"0x{result:0{hexw}X} ({result})")
        elif args.command == "explain":
            data = _parse_crc_data(args.data, args.hex)
            print(crc_explain(data, config, max_bytes=args.max_bytes))
        elif args.command == "export-c":
            print(crc_export_c(config, function_name=args.name))
        return 0

    if args.group == "registers":
        reg = _build_register(args.name, args.size, args.field)
        if args.command == "explain":
            pack_values = _parse_pack_values(args.pack) if args.pack else {}
            print(reg_explain(reg, **pack_values))
        elif args.command == "export-c":
            print(reg_export_c(reg, style=args.style))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
