import random
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from bitlab.comms import cobs_encode, export_c

GCC_AVAILABLE = shutil.which("gcc") is not None


def test_export_c_contains_expected_pieces():
    code = export_c()
    assert "#include <stdint.h>" in code
    assert "size_t cobs_encode(const uint8_t *src, size_t len, uint8_t *dst)" in code
    assert "size_t cobs_decode(const uint8_t *src, size_t len, uint8_t *dst)" in code


def test_export_c_respects_custom_function_names():
    code = export_c(encode_fn_name="my_encode", decode_fn_name="my_decode")
    assert "my_encode(const uint8_t *src" in code
    assert "my_decode(const uint8_t *src" in code


@pytest.mark.skipif(not GCC_AVAILABLE, reason="gcc not available in this environment")
def test_generated_c_round_trips_and_matches_python():
    """Compiles the generated C, then property-tests it against Python's
    cobs_encode across randomized inputs -- both for round-trip correctness
    in C and byte-exact agreement with the Python implementation."""
    code = export_c()

    harness = """
    #include <stdio.h>
    #include <string.h>
    #include <stdint.h>
    #include <stddef.h>

    size_t cobs_encode(const uint8_t *src, size_t len, uint8_t *dst);
    size_t cobs_decode(const uint8_t *src, size_t len, uint8_t *dst);

    int main(void) {
        uint8_t buf[8192];
        size_t len = fread(buf, 1, sizeof(buf), stdin);

        uint8_t encoded[8192 + 64];
        size_t enc_len = cobs_encode(buf, len, encoded);

        for (size_t i = 0; i < enc_len; i++) printf("%02x", encoded[i]);
        printf("\\n");

        uint8_t decoded[8192 + 64];
        size_t dec_len = cobs_decode(encoded, enc_len, decoded);
        int match = (dec_len == len) && (memcmp(decoded, buf, len) == 0);
        printf("%s\\n", match ? "MATCH" : "MISMATCH");
        return match ? 0 : 1;
    }
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "cobs_impl.c").write_text(code)
        (tmp / "main.c").write_text(harness)
        binary = tmp / "cobs_test_bin"

        compile_result = subprocess.run(
            ["gcc", "-O2", "-o", str(binary), str(tmp / "cobs_impl.c"), str(tmp / "main.c")],
            capture_output=True,
            text=True,
        )
        assert compile_result.returncode == 0, compile_result.stderr

        random.seed(2024)
        for _ in range(150):
            length = random.randint(0, 600)
            data = bytes(random.randrange(256) for _ in range(length))
            py_encoded = cobs_encode(data)

            run_result = subprocess.run([str(binary)], input=data, capture_output=True)
            assert run_result.returncode == 0, f"C round-trip failed for {data!r}"

            c_hex, status = run_result.stdout.decode().strip().splitlines()
            assert status == "MATCH"
            assert bytes.fromhex(c_hex) == py_encoded, f"C/Python encode mismatch for {data!r}"
