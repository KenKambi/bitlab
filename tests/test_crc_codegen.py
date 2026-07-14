import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from bitlab.crc.codegen import export_c
from bitlab.crc.presets import (
    CRC8_SMBUS,
    CRC16_CCITT_FALSE,
    CRC16_MODBUS,
    CRC32_ISO_HDLC,
)

GCC_AVAILABLE = shutil.which("gcc") is not None

ALL_PRESETS = [CRC8_SMBUS, CRC16_CCITT_FALSE, CRC16_MODBUS, CRC32_ISO_HDLC]


def test_export_c_contains_expected_pieces():
    code = export_c(CRC32_ISO_HDLC)
    assert "#include <stdint.h>" in code
    assert "static const uint32_t" in code
    assert "_table[256]" in code
    assert "uint32_t" in code


def test_export_c_respects_custom_function_name():
    code = export_c(CRC32_ISO_HDLC, function_name="my_crc32")
    assert "my_crc32(const uint8_t *data, size_t len)" in code
    assert "my_crc32_table" in code


def test_export_c_rejects_unsupported_width():
    from bitlab.crc.presets import CRCConfig

    bad = CRCConfig("crc-24-fake", 24, 0x800063, 0x0, False, False, 0x0, 0x0)
    with pytest.raises(ValueError):
        export_c(bad)


@pytest.mark.skipif(not GCC_AVAILABLE, reason="gcc not available in this environment")
@pytest.mark.parametrize("config", ALL_PRESETS, ids=lambda c: c.name)
def test_generated_c_compiles_and_matches_catalog_check_value(config):
    """The strongest possible test: actually compile the generated C and run
    it, then compare the result to the published CRC-catalogue check value."""
    fn_name = "crc_under_test"
    c_source = export_c(config, function_name=fn_name)
    hexw = config.width // 4

    harness = f"""
    #include <stdio.h>
    #include <string.h>
    #include <stdint.h>
    #include <stddef.h>

    {"uint8_t" if config.width == 8 else "uint16_t" if config.width == 16 else "uint32_t"}
    {fn_name}(const uint8_t *data, size_t len);

    int main(void) {{
        const char *msg = "123456789";
        unsigned long result = (unsigned long) {fn_name}((const uint8_t*)msg, strlen(msg));
        printf("%lu\\n", result);
        return 0;
    }}
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "crc_impl.c").write_text(c_source)
        (tmp / "main.c").write_text(harness)
        binary = tmp / "crc_test_bin"

        compile_result = subprocess.run(
            ["gcc", "-O2", "-o", str(binary), str(tmp / "crc_impl.c"), str(tmp / "main.c")],
            capture_output=True,
            text=True,
        )
        assert compile_result.returncode == 0, compile_result.stderr

        run_result = subprocess.run([str(binary)], capture_output=True, text=True)
        assert run_result.returncode == 0
        assert int(run_result.stdout.strip()) == config.check
