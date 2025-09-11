
import io, sys
from pathlib import Path
import pytest
from pyproj_inspector.cli import main as cli_main

def test_cli_json_output(tmp_path, monkeypatch):
    (tmp_path / "t.py").write_text("import os\n", encoding="utf-8")
    buf = io.StringIO()
    real = sys.stdout
    try:
        sys.stdout = buf
        cli_main([str(tmp_path), "--json"])
    finally:
        sys.stdout = real
    import json
    data = json.loads(buf.getvalue())
    assert "builtins" in data and "files" in data

def test_cli_binary_and_pypi_calls(tmp_path, monkeypatch):
    from pyproj_inspector import cli as cli_mod
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")
    def fake_create_binary(root, entry, **kw):
        p = Path(root) / "dist" / ("main.exe" if sys.platform.startswith("win") else "main")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("fake", encoding="utf-8")
        return p
    monkeypatch.setattr("pyproj_inspector.cli.build_utils.create_binary", fake_create_binary, raising=True)
    buf = io.StringIO(); real = sys.stdout
    try:
        sys.stdout = buf
        cli_mod.main([str(tmp_path), "binary", "--entry", "main.py", "--mode", "pyinstaller", "--onefile"])
    finally:
        sys.stdout = real
    assert "dist" in buf.getvalue()
    from pyproj_inspector import packaging_utils as pu
    monkeypatch.setattr(pu, "_fetch_pypi_json", lambda name: None, raising=True)
    buf = io.StringIO(); real = sys.stdout
    try:
        sys.stdout = buf
        cli_mod.main([str(tmp_path), "pypi", "--name", "my_pkg_name", "--new", "--creator", "Avi"])
    finally:
        sys.stdout = real
    assert "pyproject.toml" in buf.getvalue()
