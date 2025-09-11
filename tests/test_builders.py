
from pathlib import Path
import os
import pytest
from pyproj_inspector.build_utils import create_binary

def test_create_binary_pyinstaller_simulated(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
    def fake_check_call(args, **kwargs):
        dist = root / "dist"
        dist.mkdir(exist_ok=True)
        artifact = dist / ("app.exe" if os.name == "nt" else "app")
        artifact.write_text("fake-binary", encoding="utf-8")
    monkeypatch.setattr("subprocess.check_call", fake_check_call, raising=True)
    out = create_binary(root, "app.py", mode="pyinstaller", onefile=True)
    assert out.exists()

def test_create_binary_nuitka_simulated(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
    def fake_check_call(args, **kwargs):
        outdir = None
        for a in args:
            if isinstance(a, str) and a.startswith("--output-dir="):
                outdir = Path(a.split("=",1)[1])
        (outdir or (root / "dist")).mkdir(exist_ok=True)
        ((outdir or (root / "dist")) / "app-bin").write_text("fake", encoding="utf-8")
    monkeypatch.setattr("subprocess.check_call", fake_check_call, raising=True)
    out = create_binary(root, "app.py", mode="nuitka", onefile=True)
    assert out.exists()
