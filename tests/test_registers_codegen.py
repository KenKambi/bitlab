import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from bitlab.registers import Register, export_c

GCC_AVAILABLE = shutil.which("gcc") is not None


def make_reg() -> Register:
    reg = Register("UART_CR1", size_bits=8)
    reg.add_field("ENABLE", bit_index=0, description="Peripheral enable")
    reg.add_field("MODE", bit_range=(1, 3), description="Operating mode")
    reg.add_field("TXIE", bit_index=7, description="TX interrupt enable")
    return reg


def test_export_c_defines_contains_expected_pieces():
    code = export_c(make_reg(), style="defines")
    assert "#define UART_CR1_ENABLE_POS" in code
    assert "#define UART_CR1_MODE_MASK" in code
    assert "#define UART_CR1_SET_TXIE(reg, val)" in code
    assert "#define UART_CR1_GET_ENABLE(reg)" in code


def test_export_c_struct_contains_expected_pieces():
    code = export_c(make_reg(), style="struct")
    assert "typedef struct" in code
    assert "ENABLE : 1" in code
    assert "MODE : 3" in code
    assert "_RESERVED_" in code
    assert "implementation-defined" in code  # honest portability caveat present


def test_export_c_rejects_unknown_style():
    with pytest.raises(ValueError):
        export_c(make_reg(), style="rust")


@pytest.mark.skipif(not GCC_AVAILABLE, reason="gcc not available in this environment")
def test_generated_defines_c_compiles_and_matches_python_pack():
    reg = make_reg()
    code = export_c(reg, style="defines")
    expected = reg.pack(ENABLE=1, MODE=5, TXIE=1)

    harness = f"""
    #include <stdio.h>
    #include <stdint.h>
    {code}
    int main(void) {{
        uint8_t reg = 0;
        UART_CR1_SET_ENABLE(reg, 1);
        UART_CR1_SET_MODE(reg, 5);
        UART_CR1_SET_TXIE(reg, 1);
        printf("%u\\n", reg);
        printf("%u\\n", UART_CR1_GET_MODE(reg));
        return 0;
    }}
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "main.c").write_text(harness)
        binary = tmp / "reg_test_bin"

        compile_result = subprocess.run(
            ["gcc", "-O2", "-o", str(binary), str(tmp / "main.c")],
            capture_output=True,
            text=True,
        )
        assert compile_result.returncode == 0, compile_result.stderr

        run_result = subprocess.run([str(binary)], capture_output=True, text=True)
        assert run_result.returncode == 0
        packed_str, mode_str = run_result.stdout.strip().splitlines()
        assert int(packed_str) == expected
        assert int(mode_str) == 5


@pytest.mark.skipif(not GCC_AVAILABLE, reason="gcc not available in this environment")
def test_generated_struct_c_compiles_and_matches_python_pack_on_this_platform():
    """Confirms the struct style matches Python's pack() on this compiler/
    platform (x86-64 GCC, little-endian). This is NOT a portability
    guarantee across all compilers -- see the caveat in the generated code."""
    reg = make_reg()
    code = export_c(reg, style="struct")
    expected = reg.pack(ENABLE=1, MODE=5, TXIE=1)

    harness = f"""
    #include <stdio.h>
    #include <string.h>
    #include <stdint.h>
    {code}
    int main(void) {{
        UART_CR1_t s = {{0}};
        s.ENABLE = 1;
        s.MODE = 5;
        s.TXIE = 1;
        uint8_t raw;
        memcpy(&raw, &s, sizeof(raw));
        printf("%u\\n", raw);
        return 0;
    }}
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "main.c").write_text(harness)
        binary = tmp / "reg_struct_test_bin"

        compile_result = subprocess.run(
            ["gcc", "-O2", "-o", str(binary), str(tmp / "main.c")],
            capture_output=True,
            text=True,
        )
        assert compile_result.returncode == 0, compile_result.stderr

        run_result = subprocess.run([str(binary)], capture_output=True, text=True)
        assert run_result.returncode == 0
        assert int(run_result.stdout.strip()) == expected
