
import pytest
from pyproj_inspector.packaging_utils import plan_pypi_version, create_pypi_package

def test_pypi_plan_new_name_available(monkeypatch):
    from pyproj_inspector import packaging_utils as pu
    monkeypatch.setattr(pu, "_fetch_pypi_json", lambda name: None, raising=True)
    plan = plan_pypi_version("unique_name_xyz123", None, new=True)
    assert plan.is_new_project and plan.version == "0.1.0"

def test_pypi_plan_new_name_conflict(monkeypatch):
    from pyproj_inspector import packaging_utils as pu
    monkeypatch.setattr(pu, "_fetch_pypi_json", lambda name: {"info": {"version":"1.0.0"}}, raising=True)
    with pytest.raises(ValueError):
        plan_pypi_version("existing_project", None, new=True)

def test_pypi_plan_bump_existing(monkeypatch):
    from pyproj_inspector import packaging_utils as pu
    monkeypatch.setattr(pu, "_fetch_pypi_json", lambda name: {"info": {"version":"1.0.0"}}, raising=True)
    plan = plan_pypi_version("existing_project", None, new=False)
    assert plan.version == "1.0.1"

def test_create_pypi_package_writes_files(tmp_path, monkeypatch):
    from pyproj_inspector import packaging_utils as pu
    monkeypatch.setattr(pu, "_fetch_pypi_json", lambda name: None, raising=True)
    pyproj = create_pypi_package(tmp_path, "mypkg", version="0.2.0", new=True, creator_name="Avi Twil")
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / "mypkg" / "__init__.py").exists()
