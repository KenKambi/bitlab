"""Human-readable register layout diagrams and pack traces — the educational
counterpart to `Register.pack()`/`unpack()`.
"""

from __future__ import annotations

from .core import Register


def _bit_diagram(reg: Register) -> str:
    """Renders a datasheet-style bit diagram, e.g.:

        Bit:    7      6      5      4      3      2      1      0
        Field:  TXIE   .      .      .      MODE   MODE   MODE   ENABLE
    """
    labels = []
    for bit in range(reg.size_bits - 1, -1, -1):
        owner = None
        for field in reg.fields.values():
            if field.start <= bit <= field.end:
                owner = field.name
                break
        labels.append(owner if owner else ".")

    col_width = max([len("Bit:")] + [len(lbl) for lbl in labels] + [len(str(reg.size_bits - 1))]) + 2
    bit_numbers = "".join(str(b).ljust(col_width) for b in range(reg.size_bits - 1, -1, -1))
    field_row = "".join(lbl.ljust(col_width) for lbl in labels)

    return f"Bit:   {bit_numbers}\nField: {field_row}"


def explain(reg: Register, **pack_values: int) -> str:
    """Describes a register's layout, and (if field values are given) traces
    through packing them into a raw value.

    With no keyword arguments, returns just the layout diagram and field
    list. With `ENABLE=1, MODE=5` etc., also shows the pack computation.
    """
    lines = []
    lines.append(f"Register: {reg.name} ({reg.size_bits}-bit)")
    lines.append("")
    lines.append(_bit_diagram(reg))
    lines.append("")
    lines.append("Fields (MSB to LSB):")
    for field in reg.layout():
        bits = f"bit {field.start}" if field.width == 1 else f"bits {field.start}-{field.end}"
        desc = f" -- {field.description}" if field.description else ""
        lines.append(f"  {field.name:<12} {bits:<12} (max {field.max_value}){desc}")

    reserved = reg.reserved_ranges()
    if reserved:
        lines.append("")
        lines.append("Reserved (unassigned):")
        for start, end in reserved:
            bits = f"bit {start}" if start == end else f"bits {start}-{end}"
            lines.append(f"  {bits}")

    if pack_values:
        lines.append("")
        lines.append(f"Packing {reg.name}({', '.join(f'{k}={v}' for k, v in pack_values.items())}):")
        raw = 0
        hexw = (reg.size_bits + 3) // 4
        for name, value in pack_values.items():
            field = reg.fields[name]
            shifted = (value & field.max_value) << field.start
            raw |= shifted
            lines.append(
                f"  {name}={value} -> 0b{value:0{field.width}b} shifted left {field.start} "
                f"-> 0x{shifted:0{hexw}X}  |  running value = 0x{raw:0{hexw}X}"
            )
        lines.append("")
        lines.append(f"Final packed value: 0x{raw:0{hexw}X} (0b{raw:0{reg.size_bits}b})")

    return "\n".join(lines)
