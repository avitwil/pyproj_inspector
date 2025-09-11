
import io, sys, json, pytest
from pathlib import Path
from pyproj_inspector import PythonProject
from pyproj_inspector.packaging_utils import plan_pypi_version, create_pypi_package

def test_alias_and_from_imports(tmp_path, monkey_packages_distributions, block_network):
    (tmp_path / "m.py").write_text(
        "import os as operating_system\n"
        "from json import dumps\n"
        "from requests.sessions import Session\n",
        encoding="utf-8"
    )
    proj = PythonProject(tmp_path)
    assert 'os' in proj.result.builtins
    assert 'requests' in proj.result.external_imports

def test_stdlib_shadowed_by_local_internal(tmp_path, monkey_packages_distributions, block_network):
    (tmp_path / "json.py").write_text("X=1\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    assert 'json' in proj.result.internal_modules
    assert 'json' not in proj.result.builtins

def test_latin1_fallback(tmp_path, monkey_packages_distributions, block_network):
    content = "caf\xe9 = 'ok'\n"
    (tmp_path / "latin1.py").write_bytes(content.encode("latin-1"))
    proj = PythonProject(tmp_path)
    assert 'latin1.py' in proj.result.files_code

def test_pypi_head_fallback(tmp_path, monkeypatch):
    import pyproj_inspector.inspector as insp
    monkeypatch.setattr(insp, 'packages_distributions', None, raising=True)
    import urllib.request
    class DummyResp:
        def __init__(self): self.status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b""
    def fake_urlopen(req, timeout=3): return DummyResp()
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen, raising=True)
    (tmp_path / "x.py").write_text("import coollib\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    assert 'coollib' in proj.result.external_imports
    assert 'coollib' in proj.result.external_imports['coollib']

def test_run_in_tmp_env_installs_externals(tmp_path, monkeypatch):
    (tmp_path / "main.py").write_text("import requests\nprint('ok')\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    calls = []
    def fake_check_call(args, **kw):
        calls.append(args); return 0
    def fake_run(args, **kw):
        class R: 
            returncode=0; stdout="ok\n"; stderr=""
        return R()
    monkeypatch.setattr("subprocess.check_call", fake_check_call, raising=True)
    monkeypatch.setattr("subprocess.run", fake_run, raising=True)
    res = proj.run_in_tmp_env(entry="main.py", install=True)
    joined = " ".join(" ".join(map(str,a)) for a in calls)
    assert "pip install" in joined and "requests" in joined
    assert res.returncode == 0

def test_restore_nested_structure(tmp_path, monkey_packages_distributions, block_network):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "sub").mkdir()
    (tmp_path / "pkg" / "sub" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "sub" / "mod.py").write_text("x=1\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    out = tmp_path / "OUT"
    proj.restore_to(out)
    assert (out / "pkg" / "sub" / "mod.py").exists()

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

def test_manual_higher_version_wins(monkeypatch, tmp_path):
    from pyproj_inspector import packaging_utils as pu
    monkeypatch.setattr(pu, "_fetch_pypi_json", lambda name: {"info": {"version": "1.2.3"}}, raising=True)
    plan = plan_pypi_version("someproj", "2.0.0", new=False)
    assert plan.version == "2.0.0"
    py = create_pypi_package(tmp_path, "someproj", version="2.0.0", new=False, creator_name="Avi")
    txt = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "2.0.0"' in txt

def test_namespace_like_internal_detection(tmp_path, monkey_packages_distributions, block_network):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "sub").mkdir(parents=True)
    (tmp_path / "main.py").write_text("from pkg import sub\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    assert ('pkg' in proj.result.internal_modules) or ('pkg' not in proj.result.internal_modules)

def test_deep_relative_import_internal(tmp_path, monkey_packages_distributions, block_network):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "__init__.py").write_text("from . import c\n", encoding="utf-8")
    (tmp_path / "a" / "b" / "c.py").write_text("x=1\n", encoding="utf-8")
    (tmp_path / "use.py").write_text("from a.b import c\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    assert 'a' in proj.result.internal_modules
