
# pyproj_inspector — User Guide

*A comprehensive, feature-by-feature guide with real examples.*  
Author: **Avi Twil** • License: MIT • Python 3.8+

---

## 1. Installation

Install from PyPI (recommended):
```bash
pip install pyproj_inspector
```
> For binary creation: install `pyinstaller` or `nuitka`. For Debian packaging: ensure `dpkg-deb` exists.

## 2. Concepts & What This Tool Does

- Built-ins (stdlib) detection
- External imports → PyPI distributions (with best‑effort PyPI probe)
- Internal modules discovery from file layout + relative imports
- Full file snapshot (`relative_path -> source`)
- Optional entry script for single-file analysis
- Extras: restore snapshot, run in isolated venv, build binaries, scaffold PyPI, build `.deb`

## 3. Quickstarts
### 3.1 Single script
```python
from pyproj_inspector import PythonProject
proj = PythonProject("app.py")
print(proj.result.builtins, proj.result.external_imports, proj.result.internal_modules, proj.result.entry_relpath)
```
### 3.2 Project dir
```python
proj = PythonProject("path/to/project_dir")
print(sorted(proj.moduls()), len(proj.result.files_code))
```
### 3.3 CLI JSON
```bash
pyproj_inspector path/to/project --json
```

## 4. Python API — Features & Examples
### 4.1 `PythonProject`
Parses a `.py` file or a directory of `*.py` files; syntax‑error files are still captured in `files_code`.
### 4.2 Built-ins
Classified via `sys.stdlib_module_names` (fallback list included).
### 4.3 External imports → distributions
Mapped via `importlib.metadata.packages_distributions()`; unmapped names are probed on PyPI Simple with `HEAD`.
### 4.4 Internal modules
From file layout (top-level names); `pkg/__init__.py` → `pkg`. Relative imports mark the current package as internal. Local shadowing (e.g. `json.py`) is treated as **internal**.
### 4.5 Files snapshot
`proj.result.files_code` holds all sources; UTF‑8 with Latin‑1 fallback.
### 4.6 `moduls()`
Returns sorted internal module names.
### 4.7 `restore_to(target)`
Writes full snapshot to target directory (overwrites existing files).
### 4.8 `run_in_tmp_env(entry=None, install=True, ...)`
Creates temp venv, installs external dists (keys of `external_imports`), runs entry (`entry_relpath` / `__main__.py` / `main.py`). Returns `CompletedProcess`.
### 4.9 `create_binary(...)`
Builds a standalone binary of an entry script via **PyInstaller** or **Nuitka**. Ensure backend is installed.
### 4.10 `create_pypi_package(...)` + `plan_pypi_version(...)`
Scaffolds `pyproject.toml` and package dir. Version planning:
- `new=True`: error if name exists, else use given version or `0.1.0`.
- `new=False`: bump patch from latest unless you pass a higher version.
### 4.11 `create_debian_package(...)`
Stages project under `/usr/local/lib/<name>` and writes `DEBIAN/control`; optional launcher in `/usr/local/bin/<name>`. Requires `dpkg-deb`.

## 5. CLI Reference
### Global
```bash
pyproj_inspector PATH [--json] [SUBCOMMAND ...]
```
- `PATH`: `.py` file or project directory
- `--json`: print JSON summary (builtins, external, internal, files, entry)

### `binary`
```bash
pyproj_inspector PATH binary --entry ENTRY [--mode {pyinstaller,nuitka}] [--onefile]
```
- `--entry` (required): relative entry path inside root (e.g. `main.py`)
- `--mode` (default `pyinstaller`): choose backend
- `--onefile` (flag, default on): bundle into single file when supported

### `pypi`
```bash
pyproj_inspector PATH pypi --name NAME [--version VERSION] [--new] [--creator CREATOR]
```
- `--name` (required)
- `--version` (optional)
- `--new` (flag): check PyPI availability; if taken → error
- `--creator` (default `Unknown`)

### `deb`
```bash
pyproj_inspector PATH deb --name NAME [--version VERSION] [--creator CREATOR] [--entry ENTRY]
```
- `--name` (required), `--version` (default `0.1.0`), `--creator`
- `--entry` optional launcher

## 6. Design Notes
Discovery → file capture (UTF‑8, Latin‑1 fallback) → classify imports (internal→stdlib→external) → external mapping (metadata, PyPI HEAD) → optional venv execution.

## 7. Tips & Troubleshooting
- Shadowed stdlib names are internal by design.
- If no `main.py`/`__main__.py`, pass `--entry`.
- Install chosen backend for binary builds.
- Network-free runs: mapping may miss some external names.

## 8. Development
Run tests:
```bash
python -m pip install -U pip pytest
pytest -q
```

## 9. FAQ
- **Does it modify my project?** Only explicit write actions (`restore_to`, packaging).
- **How are versions chosen?** See section 4.10.

## 10. License & Author
MIT • **Avi Twil**
