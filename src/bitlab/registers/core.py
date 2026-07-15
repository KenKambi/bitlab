"""Hardware register bit-field mapping: define a register's layout once,
then pack named field values into a raw integer or unpack a raw integer
back into named fields.

    >>> reg = Register("UART_CR1", size_bits=8)
    >>> reg.add_field("ENABLE", bit_index=0)
    >>> reg.add_field("MODE", bit_range=(1, 3))
    >>> hex(reg.pack(ENABLE=1, MODE=0b101))
    '0xb'
    >>> reg.unpack(0xB)
    {'ENABLE': 1, 'MODE': 5}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Field:
    """A single named bit-field within a register.

    Attributes:
        name: Field name, e.g. "ENABLE".
        start: Index of the field's least-significant bit (0 = LSB of the
            register).
        width: Number of bits the field occupies.
        description: Optional human-readable description.
    """

    name: str
    start: int
    width: int
    description: Optional[str] = None

    @property
    def end(self) -> int:
        """Index of the field's most-significant bit (inclusive)."""
        return self.start + self.width - 1

    @property
    def max_value(self) -> int:
        """The largest unsigned value this field can hold."""
        return (1 << self.width) - 1

    @property
    def mask(self) -> int:
        """The field's bitmask, already shifted into register position."""
        return self.max_value << self.start


class Register:
    """Describes a register's bit-field layout and packs/unpacks values."""

    def __init__(self, name: str, size_bits: int = 8):
        if size_bits <= 0:
            raise ValueError("size_bits must be positive")
        self.name = name
        self.size_bits = size_bits
        self.fields: Dict[str, Field] = {}

    def add_field(
        self,
        name: str,
        bit_index: Optional[int] = None,
        bit_range: Optional[Tuple[int, int]] = None,
        description: Optional[str] = None,
    ) -> "Register":
        """Adds a named field to the register. Returns `self` so calls can
        be chained.

        Specify exactly one of:
            bit_index: for a single-bit field, e.g. bit_index=0.
            bit_range: an inclusive (start, end) pair, e.g. (1, 3) for a
                3-bit-wide field occupying bits 1, 2, and 3.
        """
        if name in self.fields:
            raise ValueError(f"Field {name!r} already exists on register {self.name!r}")
        if (bit_index is None) == (bit_range is None):
            raise ValueError("Specify exactly one of bit_index or bit_range")

        if bit_index is not None:
            start, width = bit_index, 1
        else:
            start, end = bit_range
            if end < start:
                raise ValueError(f"bit_range end ({end}) must be >= start ({start})")
            width = end - start + 1

        if start < 0 or start + width > self.size_bits:
            raise ValueError(
                f"Field {name!r} (bits {start}-{start + width - 1}) doesn't fit in a "
                f"{self.size_bits}-bit register"
            )

        new_field = Field(name, start, width, description)
        for existing in self.fields.values():
            if new_field.mask & existing.mask:
                raise ValueError(
                    f"Field {name!r} (bits {start}-{start + width - 1}) overlaps "
                    f"existing field {existing.name!r} (bits {existing.start}-{existing.end})"
                )

        self.fields[name] = new_field
        return self

    def layout(self) -> List[Field]:
        """Returns all fields ordered from most-significant to least-significant bit."""
        return sorted(self.fields.values(), key=lambda f: f.start, reverse=True)

    def pack(self, **values: int) -> int:
        """Packs named field values into a single raw register value.

        Unspecified fields default to 0. Raises ValueError for unknown
        field names or out-of-range values.
        """
        raw = 0
        for name, value in values.items():
            if name not in self.fields:
                raise ValueError(
                    f"Unknown field {name!r} on register {self.name!r}. "
                    f"Known fields: {', '.join(self.fields)}"
                )
            field = self.fields[name]
            if not (0 <= value <= field.max_value):
                raise ValueError(
                    f"Value {value} out of range for field {name!r} "
                    f"({field.width}-bit, max {field.max_value})"
                )
            raw |= (value & field.max_value) << field.start
        return raw

    def unpack(self, raw: int) -> Dict[str, int]:
        """Unpacks a raw register value into a dict of {field_name: value}."""
        return {
            name: (raw >> field.start) & field.max_value
            for name, field in self.fields.items()
        }

    def get_field(self, raw: int, name: str) -> int:
        """Reads a single field's value out of a raw register value."""
        if name not in self.fields:
            raise ValueError(f"Unknown field {name!r} on register {self.name!r}")
        field = self.fields[name]
        return (raw >> field.start) & field.max_value

    def set_field(self, raw: int, name: str, value: int) -> int:
        """Returns a copy of `raw` with a single field set to `value`
        (read-modify-write; other fields/bits are preserved)."""
        if name not in self.fields:
            raise ValueError(f"Unknown field {name!r} on register {self.name!r}")
        field = self.fields[name]
        if not (0 <= value <= field.max_value):
            raise ValueError(
                f"Value {value} out of range for field {name!r} "
                f"({field.width}-bit, max {field.max_value})"
            )
        cleared = raw & ~field.mask
        return cleared | ((value & field.max_value) << field.start)

    def reserved_ranges(self) -> List[Tuple[int, int]]:
        """Returns the (start, end) inclusive bit ranges NOT covered by any
        field, highest-bit-first."""
        covered = [False] * self.size_bits
        for field in self.fields.values():
            for bit in range(field.start, field.start + field.width):
                covered[bit] = True

        ranges = []
        bit = self.size_bits - 1
        while bit >= 0:
            if not covered[bit]:
                end = bit
                while bit >= 0 and not covered[bit]:
                    bit -= 1
                start = bit + 1
                ranges.append((start, end))
            else:
                bit -= 1
        return ranges
