# Contributing to bitlab

## Development setup

```bash
git clone https://github.com/KenKambi/bitlab.git
cd bitlab
pip install -e ".[dev]"
pytest
```

Each submodule (`bitutils`, `parity`, `crc`) has its own test file(s) under
`tests/`. `test_crc_codegen.py` compiles the generated C with `gcc` and
actually runs it — install `gcc` locally (`apt install gcc` / Xcode Command
Line Tools / MinGW) or those specific tests will be skipped automatically.

## Project layout

```
src/bitlab/
├── bitutils/   # foundational bit ops — add here only if it's used by 2+ other submodules
├── parity/     # parity + Hamming(7,4)
└── crc/        # engine.py (compute), presets.py (CRCConfig + built-ins),
                # explain.py (educational trace), codegen.py (C export)
```

When adding a new domain (e.g. registers, arch, comms), give it its own
top-level submodule under `src/bitlab/`, following the same pattern as
`crc/`: a `presets.py`/config layer, a computation engine, and — where it
makes sense — an `explain()` and/or `export_c()`.

## Before opening a PR

```bash
pytest -v                 # all tests must pass
python -m build             # package must build cleanly
python -m twine check dist/*  # metadata must be valid
```

CI runs the same checks across Python 3.9–3.13 on every push/PR.

