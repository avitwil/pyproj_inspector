
import json
from pyproj_inspector import PythonProject

def test_inspector_basic_script(sample_project, monkey_packages_distributions, block_network):
    proj = PythonProject(sample_project)
    assert 'os' in proj.result.builtins
    assert 'json' in proj.result.builtins
    assert 'utils' in proj.result.internal_modules
    assert 'requests' in proj.result.external_imports
    assert 'requests' in proj.result.external_imports['requests']
    assert 'app.py' in proj.result.files_code
    assert 'utils.py' in proj.result.files_code
    js = json.loads(proj.result.to_json())
    assert 'builtins' in js and 'external_imports' in js and 'internal_modules' in js and 'files' in js

def test_moduls_lists_internal(sample_project, monkey_packages_distributions, block_network):
    proj = PythonProject(sample_project)
    assert set(proj.moduls()) >= {'utils'}  # may include 'app' too

def test_restore_to_materializes_files(sample_project, monkey_packages_distributions, block_network, tmp_path):
    proj = PythonProject(sample_project)
    out = proj.restore_to(tmp_path / "materialized")
    assert (out / "app.py").exists()
    assert (out / "utils.py").exists()

def test_run_in_tmp_env_executes_entry(sample_project, monkey_packages_distributions, block_network):
    (sample_project / "runner.py").write_text("print('OK_RUN')\n", encoding="utf-8")
    proj = PythonProject(sample_project)
    res = proj.run_in_tmp_env(entry="runner.py", install=False)
    assert res.returncode == 0
    assert "OK_RUN" in (res.stdout or "")
