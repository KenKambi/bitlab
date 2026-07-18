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

    bitlab registers explain --name NAME --size BITS --field NAME:BIT [--field ...] [--pack NAME=VAL,...]
    bitlab registers export-c --name NAME --size BITS --field NAME:BIT [--field ...] [--style defines|struct]

    bitlab arch float <value> [--width 32|64]
    bitlab arch endian <value> [--width-bytes N]
    bitlab arch gray-encode <value> [--width N]
    bitlab arch gray-decode <value> [--width N]
    bitlab arch q-encode <value> [--format Qm.n] [--saturate]
    bitlab arch q-decode <value> [--format Qm.n]

    bitlab comms cobs-encode <hex_data>
    bitlab comms cobs-decode <hex_data>
    bitlab comms cobs-explain <hex_data> [--max-blocks N]
    bitlab comms export-c [--encode-name NAME] [--decode-name NAME]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict

from .arch.explain import explain_endianness, explain_fixed_point, explain_float, explain_gray
from .arch.fixed_point import q_to_float
from .arch.gray import binary_to_gray, gray_to_binary
from .comms.cobs import cobs_decode, cobs_encode
from .comms.codegen import export_c as comms_export_c
from .comms.explain import explain_cobs
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

    # --- arch ---
    arch_parser = subparsers.add_parser("arch", help="Computer architecture toolkit")
    arch_sub = arch_parser.add_subparsers(dest="command")

    float_p = arch_sub.add_parser("float", help="Decompose a float into IEEE 754 fields")
    float_p.add_argument("value", type=float)
    float_p.add_argument("--width", type=int, choices=[32, 64], default=32)

    endian_p = arch_sub.add_parser("endian", help="Swap byte order of an integer")
    endian_p.add_argument("value", type=str, help="Integer value (decimal, 0b, or 0x)")
    endian_p.add_argument("--width-bytes", type=int, default=4)

    gray_encode_p = arch_sub.add_parser("gray-encode", help="Binary -> Gray code")
    gray_encode_p.add_argument("value", type=str)
    gray_encode_p.add_argument("--width", type=int, default=8)

    gray_decode_p = arch_sub.add_parser("gray-decode", help="Gray code -> binary")
    gray_decode_p.add_argument("value", type=str)
    gray_decode_p.add_argument("--width", type=int, default=8)

    q_encode_p = arch_sub.add_parser("q-encode", help="Float -> Q-format fixed-point")
    q_encode_p.add_argument("value", type=float)
    q_encode_p.add_argument("--format", type=str, default="Q8.8", dest="q_format")
    q_encode_p.add_argument("--saturate", action="store_true")

    q_decode_p = arch_sub.add_parser("q-decode", help="Q-format fixed-point -> float")
    q_decode_p.add_argument("value", type=str)
    q_decode_p.add_argument("--format", type=str, default="Q8.8", dest="q_format")

    # --- comms ---
    comms_parser = subparsers.add_parser("comms", help="Protocol framing (COBS)")
    comms_sub = comms_parser.add_subparsers(dest="command")

    cobs_encode_p = comms_sub.add_parser("cobs-encode", help="COBS-encode hex data")
    cobs_encode_p.add_argument("data", type=str, help="Hex-encoded input bytes, e.g. 11220033")

    cobs_decode_p = comms_sub.add_parser("cobs-decode", help="COBS-decode hex data")
    cobs_decode_p.add_argument("data", type=str, help="Hex-encoded COBS-encoded bytes")

    cobs_explain_p = comms_sub.add_parser("cobs-explain", help="Step-by-step COBS encode trace")
    cobs_explain_p.add_argument("data", type=str, help="Hex-encoded input bytes")
    cobs_explain_p.add_argument("--max-blocks", type=int, default=6)

    comms_export_p = comms_sub.add_parser("export-c", help="Export COBS encode/decode as C source")
    comms_export_p.add_argument("--encode-name", type=str, default="cobs_encode")
    comms_export_p.add_argument("--decode-name", type=str, default="cobs_decode")

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

    if args.group == "arch":
        if args.command == "float":
            print(explain_float(args.value, width=args.width))
        elif args.command == "endian":
            value = _parse_number(args.value)
            print(explain_endianness(value, args.width_bytes))
        elif args.command == "gray-encode":
            value = _parse_number(args.value)
            result = binary_to_gray(value)
            print(f"{result} (0b{result:0{args.width}b})")
        elif args.command == "gray-decode":
            value = _parse_number(args.value)
            result = gray_to_binary(value)
            print(f"{result} (0b{result:0{args.width}b})")
        elif args.command == "q-encode":
            print(explain_fixed_point(args.value, args.q_format))
        elif args.command == "q-decode":
            raw = _parse_number(args.value)
            print(q_to_float(raw, args.q_format))
        return 0

    if args.group == "comms":
        if args.command == "cobs-encode":
            data = bytes.fromhex(args.data)
            print(cobs_encode(data).hex())
        elif args.command == "cobs-decode":
            data = bytes.fromhex(args.data)
            print(cobs_decode(data).hex())
        elif args.command == "cobs-explain":
            data = bytes.fromhex(args.data)
            print(explain_cobs(data, max_blocks=args.max_blocks))
        elif args.command == "export-c":
            print(comms_export_c(encode_fn_name=args.encode_name, decode_fn_name=args.decode_name))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
