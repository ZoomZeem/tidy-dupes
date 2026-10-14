import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    "check_deploy_sync", pathlib.Path(__file__).parent / "tools" / "check_deploy_sync.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def build(root, tweak=None):
    for mine, theirs in sync.PAIRS:
        for base in (root / "here", root / "sb" / "apps" / "tidy"):
            p = base / (mine if base.name == "here" else theirs)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("same")
    if tweak:
        tweak(root)


def test_in_sync(tmp_path):
    build(tmp_path)
    assert sync.compare(tmp_path / "here", tmp_path / "sb") == []


def test_detects_drift_and_missing(tmp_path):
    def tweak(r):
        (r / "sb" / "apps" / "tidy" / "site" / "index.html").write_text("drifted")
        (r / "sb" / "apps" / "tidy" / "sample_dup.json").unlink()
    build(tmp_path, tweak)
    assert sync.compare(tmp_path / "here", tmp_path / "sb") == [
        "missing: sample_dup.json (sandbox)", "differs: site/index.html"]
