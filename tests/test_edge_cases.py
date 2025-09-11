
import pytest
from pathlib import Path
from pyproj_inspector import PythonProject
from pyproj_inspector.build_utils import create_binary
from pyproj_inspector.packaging_utils import create_debian_package

def test_single_file_entry_detection(tmp_path, monkey_packages_distributions, block_network):
    f = tmp_path / "solo.py"
    f.write_text("import os\nprint('x')\n", encoding="utf-8")
    proj = PythonProject(f)
    assert proj.result.entry_relpath == "solo.py"
    assert 'os' in proj.result.builtins
    assert 'solo.py' in proj.result.files_code

def test_syntax_error_file_is_kept(tmp_path, monkey_packages_distributions, block_network):
    bad = tmp_path / "bad.py"
    bad.write_text("def x(:\n    pass\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    assert 'bad.py' in proj.result.files_code

def test_relative_import_marks_internal(tmp_path, monkey_packages_distributions, block_network):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("from . import mod\n", encoding="utf-8")
    (tmp_path / "pkg" / "mod.py").write_text("x=1\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    assert 'pkg' in proj.result.internal_modules

def test_packages_distributions_absent(tmp_path, monkeypatch, block_network):
    import pyproj_inspector.inspector as insp
    monkeypatch.setattr(insp, 'packages_distributions', None, raising=True)
    (tmp_path / "app.py").write_text("import requests\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    assert proj.result.external_imports == {}

def test_create_binary_invalid_entry_raises(tmp_path):
    (tmp_path / "src").mkdir()
    with pytest.raises(FileNotFoundError):
        create_binary(tmp_path / "src", "nope.py", mode="pyinstaller")

def test_debian_package_simulated(tmp_path, monkeypatch):
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    def fake_check_call(args, **kwargs):
        deb_path = Path(args[-1])
        deb_path.write_text("fake-deb", encoding="utf-8")
    monkeypatch.setattr("subprocess.check_call", fake_check_call, raising=True)
    deb = create_debian_package(tmp_path / "p", "mypkg", version="0.0.1", creator_name="Avi", entry=None)
    assert deb.exists() and deb.name == "mypkg_0.0.1.deb"

def test_restore_overwrite(tmp_path, monkey_packages_distributions, block_network):
    (tmp_path / "a.py").write_text("print(1)\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    (out / "a.py").write_text("OLD\n", encoding="utf-8")
    proj.restore_to(out)
    assert (out / "a.py").read_text(encoding="utf-8").startswith("print(1)")

def test_large_project_many_files(tmp_path, monkey_packages_distributions, block_network):
    for i in range(50):
        (tmp_path / f"m{i}.py").write_text(f"import os\nX{i}=1\n", encoding="utf-8")
    proj = PythonProject(tmp_path)
    assert len(proj.result.files_code) >= 50
