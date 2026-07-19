import random
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from bitlab.ecc import rs_encode
from bitlab.ecc.codegen import export_c_encoder

GCC_AVAILABLE = shutil.which("gcc") is not None


def test_export_contains_expected_pieces():
    code = export_c_encoder(10)
    assert "#include <stdint.h>" in code
    assert "void rs_encode(const uint8_t *data, size_t len, uint8_t *out)" in code
    assert "static const uint8_t rs_encode_gf_exp[512]" in code


def test_export_respects_custom_function_name():
    code = export_c_encoder(10, function_name="my_rs_enc")
    assert "void my_rs_enc(const uint8_t *data, size_t len, uint8_t *out)" in code


def test_export_rejects_invalid_nsym():
    with pytest.raises(ValueError):
        export_c_encoder(0)
    with pytest.raises(ValueError):
        export_c_encoder(255)


@pytest.mark.skipif(not GCC_AVAILABLE, reason="gcc not available in this environment")
@pytest.mark.parametrize("nsym", [2, 8, 16, 32])
def test_generated_encoder_compiles_and_matches_python(nsym):
    code = export_c_encoder(nsym, function_name="rs_enc")

    harness = f"""
    #include <stdio.h>
    #include <stdint.h>
    #include <stddef.h>
    void rs_enc(const uint8_t *data, size_t len, uint8_t *out);
    int main(void) {{
        uint8_t buf[512];
        size_t len = fread(buf, 1, sizeof(buf), stdin);
        uint8_t out[512 + {nsym}];
        rs_enc(buf, len, out);
        for (size_t i = 0; i < len + {nsym}; i++) printf("%02x", out[i]);
        printf("\\n");
        return 0;
    }}
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "rs_impl.c").write_text(code)
        (tmp / "main.c").write_text(harness)
        binary = tmp / "rs_test_bin"

        compile_result = subprocess.run(
            ["gcc", "-O2", "-o", str(binary), str(tmp / "rs_impl.c"), str(tmp / "main.c")],
            capture_output=True,
            text=True,
        )
        assert compile_result.returncode == 0, compile_result.stderr

        random.seed(9)
        for _ in range(50):
            msg_len = random.randint(1, 255 - nsym)
            data = bytes(random.randrange(256) for _ in range(msg_len))
            py_result = rs_encode(data, nsym)

            run_result = subprocess.run([str(binary)], input=data, capture_output=True)
            assert run_result.returncode == 0
            c_result = bytes.fromhex(run_result.stdout.decode().strip())
            assert c_result == py_result, f"mismatch for len={msg_len}"
