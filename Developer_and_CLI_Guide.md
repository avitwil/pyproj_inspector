
# pyproj_inspector — Developer & CLI Guide
**Author:** Avi Twil • **License:** MIT • **Python:** 3.8+ • **OS:** Windows / macOS / Linux

This guide explains every feature of `pyproj_inspector` for both **Python developers (API)** and **command‑line users (CLI)**.  
It includes detailed flag descriptions, JSON output reference, and examples for each method and command.

---

## 1) Installation

Install from PyPI:
```bash
pip install pyproj_inspector
```
Optional backends / system tools:
- **Binaries**: `pip install pyinstaller` *or* `pip install nuitka`
- **Debian packages**: ensure `dpkg-deb` exists on your system

---

## 2) What the tool does (mental model)

Given a **single .py script** or a **project directory**, the tool:
- Parses all `.py` files (UTF‑8 with Latin‑1 fallback)
- Extracts and classifies imports as **builtins (stdlib)**, **external (PyPI)**, or **internal (your project)**
- Builds an in‑memory snapshot of files (`relative/path.py -> source`)
- Detects an **entry script** if a single file was analyzed
- Lets you:
  - list internal modules (`moduls()`)
  - rehydrate sources to disk (`restore_to(...)`)
  - run your app in an isolated temp venv (`run_in_tmp_env(...)`)
  - build binaries (PyInstaller/Nuitka)
  - scaffold PyPI packaging (write `pyproject.toml`)
  - build a Debian `.deb`

**Classification priority:** internal → stdlib → external  
Example: if your project contains a `json.py` at top‑level, `json` is treated as **internal**, not stdlib.

---

## 3) Python API — Full Reference

### 3.1 Import surface
```python
from pyproj_inspector import (
    PythonProject, ProjectParseResult,
    create_binary,                 # build_utils
    create_pypi_package,           # packaging_utils
    create_debian_package,         # packaging_utils
)
from pyproj_inspector.packaging_utils import plan_pypi_version
```

### 3.2 `PythonProject`
```python
PythonProject(path: str | os.PathLike)
```
- **path**: either a single `.py` file (then `entry_relpath` is that filename) **or** a directory (recursively scans all `*.py`).

#### Core behavior
- Captures source code for each discovered file in memory (`files_code`).
- Files with **syntax errors** still appear in `files_code`; the AST pass simply skips their imports.
- Internal module names are inferred from the **file layout**, e.g. `pkg/__init__.py` → `pkg`.
- Relative imports (e.g. `from . import x`) mark the current package as **internal**.

#### Attributes via `ProjectParseResult`
```python
@dataclass
class ProjectParseResult:
    root: Path
    builtins: set[str]                          # stdlib modules seen in imports
    external_imports: dict[str, set[str]]       # dist_name -> {top-level import names}
    internal_modules: set[str]                  # top-level modules/packages in your project
    files_code: dict[str, str]                  # 'relative/path.py' -> source text
    entry_relpath: str | None                   # single-file analysis only
```
Utility:
```python
to_json() -> str  # JSON with paths and names only (no source text)
```

#### Methods
- `moduls() -> list[str]`  
  Returns a **sorted** list of internal module names (top‑level modules/packages detected in the tree).

- `restore_to(target: str | os.PathLike) -> Path`  
  Writes all files (from `files_code`) to `target`, preserving relative paths. **Overwrites** existing files.

- `run_in_tmp_env(entry: str | None = None, *, install: bool = True, env: dict[str,str] | None = None, args: list[str] | None = None, python: str | None = None) -> subprocess.CompletedProcess`  
  Creates a temp directory, rehydrates sources, bootstraps a venv, optionally installs **external distributions** (keys of `external_imports`), and runs the entry script.
  - **Entry selection**:  
    1) provided `entry`, else  
    2) `entry_relpath` when analyzing a single file, else  
    3) `__main__.py` or `main.py` if present.  
    If the chosen entry is missing from the snapshot → `FileNotFoundError`.
  - **install=True**: installs each **distribution key** from `external_imports` (e.g., `requests`) into the temp venv.
  - **python**: path to a Python interpreter to create the venv with (defaults to current).

##### Examples
```python
# Analyze a single script
proj = PythonProject("app.py")
print(proj.result.builtins)         # {'os','json',...}
print(proj.result.external_imports) # {'requests': {'requests'}}
print(proj.moduls())                # ['app']

# Analyze a directory
proj = PythonProject("path/to/project")
print(len(proj.result.files_code))  # number of .py files

# Rehydrate snapshot
out_dir = proj.restore_to("materialized/")

# Run in a temp venv
res = proj.run_in_tmp_env(entry="main.py", install=True, args=["--debug"])
print(res.returncode, res.stdout)
```

---

### 3.3 Build utilities — `create_binary(...)`
```python
from pyproj_inspector import create_binary

create_binary(
    project_root: str | os.PathLike,
    entry: str,
    *, 
    mode: Literal["pyinstaller", "nuitka"] = "pyinstaller",
    onefile: bool = True,
    output_dir: str | os.PathLike | None = None,
    extra_args: list[str] | None = None,
) -> pathlib.Path
```
- **mode**: builder backend (install one of them separately)
  - `pyinstaller` → `pip install pyinstaller`
  - `nuitka` → `pip install nuitka`
- **onefile**: bundle into a single executable when supported (PyInstaller/Nuitka).
- **output_dir**: defaults to `<project_root>/dist`.

**Returns**: path to the produced artifact.

**Example**
```python
artifact = create_binary("project", "main.py", mode="pyinstaller", onefile=True)
print("Wrote:", artifact)
```

---

### 3.4 Packaging utilities
#### 3.4.1 `plan_pypi_version(...)`
```python
from pyproj_inspector.packaging_utils import plan_pypi_version
plan = plan_pypi_version(name: str, version: str | None, new: bool)
print(plan.name, plan.version, plan.is_new_project)
```
Versioning rules:
- `new=True` → check PyPI for name availability.  
  - If exists → **ValueError**  
  - If free → use provided `version` or default **`0.1.0`**
- `new=False` → fetch latest version of `name` from PyPI.  
  - If none exists → treat as new, default `0.1.0` (or provided `version`)  
  - Else **bump patch** (e.g., `1.0.0 → 1.0.1`) unless you pass a **higher** `version`

#### 3.4.2 `create_pypi_package(...)`
```python
from pyproj_inspector import create_pypi_package

create_pypi_package(
    project_root: str | Path,
    package_name: str,
    *,
    version: str | None = None,
    new: bool = True,
    creator_name: str = "Unknown",
    description: str = "Auto-generated package",
    homepage: str = "",
) -> Path
```
Writes a **`pyproject.toml`** (PEP 621) and creates `<package_name>/__init__.py` (plus `README.md` if missing).  
Template is rendered with `string.Template` to avoid brace‑format exceptions.

**Example**
```python
toml = create_pypi_package(
    project_root="project",
    package_name="cool_pkg",
    version="0.2.0",
    new=True,
    creator_name="Avi Twil",
    description="My awesome package",
    homepage="https://example.com",
)
print("pyproject written at:", toml)
```

#### 3.4.3 `create_debian_package(...)`
```python
from pyproj_inspector import create_debian_package

create_debian_package(
    project_root: str | Path,
    package_name: str,
    *,
    version: str = "0.1.0",
    creator_name: str = "Unknown",
    entry: str | None = None,
) -> Path
```
Stages your project under `/usr/local/lib/<package_name>` with a minimal `DEBIAN/control`.  
If `entry` is provided, creates a simple launcher under `/usr/local/bin/<package_name>`.  
**Requires**: `dpkg-deb` on the system.

---

## 4) CLI — Full Reference

### 4.1 Synopsis
```bash
pyproj_inspector PATH [--json] [SUBCOMMAND ...]
```
- **PATH**: a `.py` file or a project directory
- **--json**: when used **without** a subcommand, prints JSON analysis (see [JSON schema](#5-json-output-schema))

### 4.2 Subcommands & Flags

#### `binary`
```bash
pyproj_inspector PATH binary --entry ENTRY [--mode {pyinstaller,nuitka}] [--onefile]
```
**Flags**
- `--entry ENTRY` (required)  
  Relative path to the entry script within `PATH` (e.g., `main.py`). The file **must** exist in the analyzed snapshot.
- `--mode {pyinstaller,nuitka}` (optional; default: `pyinstaller`)  
  Backend to use. Install it yourself via pip.
- `--onefile` (flag; default: enabled)  
  Bundle into a single executable where supported. *(In the current CLI, this flag defaults to “on”; it exists primarily for clarity and forwards‑compatibility.)*

**Output**
- Prints the final artifact path (usually under `<PATH>/dist`).

**Examples**
```bash
pyproj_inspector . binary --entry main.py --mode pyinstaller --onefile
pyproj_inspector src binary --entry app.py --mode nuitka
```

#### `pypi`
```bash
pyproj_inspector PATH pypi --name NAME [--version VERSION] [--new] [--creator CREATOR]
```
**Flags**
- `--name NAME` (required)  
  The distribution/package name to appear in `pyproject.toml` and on PyPI.
- `--version VERSION` (optional)  
  Semantic version. If omitted, rules under **plan_pypi_version** are applied.
- `--new` (flag; default: off)  
  Check that `NAME` is **available** on PyPI; if taken, the command errors.
- `--creator CREATOR` (optional; default: `Unknown`)  
  Author name inserted into `pyproject.toml`.

**Output**
- Prints the path to the written `pyproject.toml`.

**Examples**
```bash
pyproj_inspector . pypi --name cool_pkg --new --creator "Avi Twil"
pyproj_inspector . pypi --name cool_pkg --version 2.0.0 --creator "Avi Twil"
```

#### `deb`
```bash
pyproj_inspector PATH deb --name NAME [--version VERSION] [--creator CREATOR] [--entry ENTRY]
```
**Flags**
- `--name NAME` (required)  
  Debian package name.
- `--version VERSION` (optional; default: `0.1.0`)
- `--creator CREATOR` (optional; default: `Unknown`)
- `--entry ENTRY` (optional)  
  If provided, creates a launcher script `/usr/local/bin/NAME` that runs `ENTRY` via `python3`.

**Output**
- Prints the path to the generated `.deb` file (`NAME_VERSION.deb`) in the project root.

**Example**
```bash
pyproj_inspector . deb --name cool_tool --version 0.3.0 --creator "Avi Twil" --entry main.py
```

---

## 5) JSON output schema

When you run:
```bash
pyproj_inspector PATH --json
```
you’ll receive a JSON document like:
```json
{
  "root": "C:/path/to/project",
  "builtins": ["json", "os", "pathlib"],
  "external_imports": {
    "requests": ["requests"]
  },
  "internal_modules": ["app", "utils"],
  "files": ["app.py", "utils.py", "pkg/__init__.py"],
  "entry": "app.py"
}
```

**Fields**
- **root** *(string)*: absolute path to the analyzed root.
- **builtins** *(array of strings)*: stdlib modules detected in imports.
- **external_imports** *(object)*:  
  - **keys**: distribution names (what you `pip install`, e.g. `"requests"`).  
  - **values**: array of **top‑level import names** that mapped to this distribution.
- **internal_modules** *(array of strings)*: top‑level modules/packages inferred from the project’s file layout (plus relative‑import hints). `pkg/__init__.py` is represented as `"pkg"`.
- **files** *(array of strings)*: relative paths of all discovered `.py` files.  
  *(Note: for safety and size, raw source text is **not** embedded in the JSON. Use the Python API to access `files_code`.)*
- **entry** *(string or null)*: entry script name if a single `.py` file was analyzed; otherwise `null` unless your project explicitly includes `main.py`/`__main__.py` and you use it with `run_in_tmp_env`.

---

## 6) Recipes & Examples

### A) Inspect, then run with venv
```python
proj = PythonProject("myproj")
print("External dists:", list(proj.result.external_imports))
res = proj.run_in_tmp_env(entry="main.py", install=True)
print(res.returncode, res.stdout)
```

### B) Build a single‑file executable (Windows/macOS/Linux)
```python
from pyproj_inspector import create_binary
exe_path = create_binary("myproj", "main.py", mode="pyinstaller", onefile=True)
print(exe_path)
```

### C) Prepare for publishing to PyPI
```python
from pyproj_inspector import create_pypi_package
toml = create_pypi_package("myproj", "awesome_pkg", version="0.1.0", new=True, creator_name="Avi Twil")
print("Wrote:", toml)
```

### D) Create a Debian .deb
```bash
pyproj_inspector myproj deb --name awesome_pkg --version 0.1.0 --creator "Avi Twil" --entry main.py
```

---

## 7) Errors & Troubleshooting

- **`FileNotFoundError: Entry script 'X' was not found in parsed files`**  
  The chosen entry is not part of the analyzed snapshot. Verify the path relative to the provided `PATH`.
- **Binary build fails**  
  Make sure the selected backend is installed (`pip show pyinstaller` / `pip show nuitka`). Check platform notes of those tools.
- **`ValueError: Project name 'X' already exists on PyPI` (pypi subcommand)**  
  Pick a different `--name` or omit `--new` and provide a higher `--version` for an existing project.
- **Misclassified imports**  
  A local module shadowing stdlib (e.g., `json.py`) is intentionally treated as **internal**.

---

## 8) Development notes

Project layout:
```
pyproj_inspector/
  __init__.py
  inspector.py         # analysis core
  build_utils.py       # binary builders
  packaging_utils.py   # PyPI/DEB helpers
  cli.py               # command-line interface
tests/                 # unit & edge-case tests
pyproject.toml
README.md
```
Run tests:
```bash
python -m pip install -U pip pytest
pytest -q
```

---

## 9) FAQ

**Q:** Does `--json` include source code?  
**A:** No. It includes only paths and names. Use the Python API (`files_code`) if you need sources.

**Q:** Can I force installing extras when running in venv?  
**A:** The tool installs only the distribution **keys** it detected (e.g., `requests`). If you need extras (`requests[socks]`) or pins, install them manually in the created venv or adapt your entry script.

**Q:** Namespace packages (PEP 420)?  
**A:** Not fully supported yet; top-level dirs without `__init__.py` may not always be inferred as packages.

---

## 10) Credits

**Author:** Avi Twil
