import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from bitlab.arch import export_c_endian_swap, export_c_fixed_point, float_to_q, swap_endianness

GCC_AVAILABLE = shutil.which("gcc") is not None


def test_export_c_endian_swap_contains_expected_pieces():
    code = export_c_endian_swap(4, function_name="my_swap32")
    assert "static inline uint32_t my_swap32(uint32_t value)" in code


def test_export_c_endian_swap_rejects_unsupported_width():
    with pytest.raises(ValueError):
        export_c_endian_swap(3)


def test_export_c_fixed_point_contains_expected_pieces():
    code = export_c_fixed_point("Q1.15")
    assert "#define Q1_15_SCALE (32768)" in code
    assert "Q1_15_FROM_FLOAT" in code
    assert "Q1_15_TO_FLOAT" in code


@pytest.mark.skipif(not GCC_AVAILABLE, reason="gcc not available in this environment")
@pytest.mark.parametrize("width_bytes", [2, 4, 8])
def test_generated_endian_swap_compiles_and_matches_python(width_bytes):
    fn_name = "swap_under_test"
    code = export_c_endian_swap(width_bytes, function_name=fn_name)
    ctype = {2: "uint16_t", 4: "uint32_t", 8: "uint64_t"}[width_bytes]
    test_value = int("0x" + "".join(f"{i:X}" for i in range(1, width_bytes + 1)), 16)
    expected = swap_endianness(test_value, width_bytes)

    harness = f"""
    #include <stdio.h>
    #include <stdint.h>
    {code}
    int main(void) {{
        {ctype} result = {fn_name}(({ctype})0x{test_value:X}ULL);
        printf("%llu\\n", (unsigned long long) result);
        return 0;
    }}
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "main.c").write_text(harness)
        binary = tmp / "endian_test_bin"
        compile_result = subprocess.run(
            ["gcc", "-O2", "-o", str(binary), str(tmp / "main.c")],
            capture_output=True, text=True,
        )
        assert compile_result.returncode == 0, compile_result.stderr
        run_result = subprocess.run([str(binary)], capture_output=True, text=True)
        assert run_result.returncode == 0
        assert int(run_result.stdout.strip()) == expected


@pytest.mark.skipif(not GCC_AVAILABLE, reason="gcc not available in this environment")
def test_generated_fixed_point_compiles_and_matches_python():
    code = export_c_fixed_point("Q1.15")
    expected = float_to_q(0.5, "Q1.15")

    harness = f"""
    #include <stdio.h>
    #include <stdint.h>
    {code}
    int main(void) {{
        int16_t raw = Q1_15_FROM_FLOAT(0.5);
        printf("%d\\n", raw);
        return 0;
    }}
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "main.c").write_text(harness)
        binary = tmp / "q_test_bin"
        compile_result = subprocess.run(
            ["gcc", "-O2", "-o", str(binary), str(tmp / "main.c")],
            capture_output=True, text=True,
        )
        assert compile_result.returncode == 0, compile_result.stderr
        run_result = subprocess.run([str(binary)], capture_output=True, text=True)
        assert run_result.returncode == 0
        assert int(run_result.stdout.strip()) == expected
