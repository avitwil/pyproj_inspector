
import sys, pathlib, pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture
def sample_project(tmp_path):
    p = tmp_path / "project"
    p.mkdir()
    (p / "utils.py").write_text("def add(a,b):\n    return a+b\n", encoding="utf-8")
    (p / "app.py").write_text(
        "import os, json\nimport requests\nfrom utils import add\n\n"
        "if __name__ == '__main__':\n    print(add(2,3))\n",
        encoding="utf-8"
    )
    return p

@pytest.fixture
def monkey_packages_distributions(monkeypatch):
    import pyproj_inspector.inspector as insp
    def fake_packages_distributions():
        return {'requests': ['requests']}
    monkeypatch.setattr(insp, 'packages_distributions', fake_packages_distributions, raising=True)
    return True

@pytest.fixture
def block_network(monkeypatch):
    import urllib.request
    def fail(*a, **k):
        raise RuntimeError("network disabled in tests")
    monkeypatch.setattr(urllib.request, "urlopen", fail, raising=True)
    return True
