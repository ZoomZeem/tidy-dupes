import json
import os
import shutil
import subprocess
import sys

import pytest

import tidy_dupes as t

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    with open(os.path.join(HERE, "sample_dup.json"), encoding="utf-8") as fh:
        return json.load(fh)


def test_parse_groups_finds_one_pair():
    groups = t.parse_groups(load())
    assert len(groups) == 1 and len(groups[0]) == 2


def test_single_file_groups_ignored():
    assert t.parse_groups({"10": [[{"path": "/a", "size": 10}]]}) == []


def test_plan_keeps_oldest_then_shortest_path():
    grp = [
        {"path": "/x/long_name.jpg", "modified_date": 5, "size": 100},
        {"path": "/x/a.jpg", "modified_date": 5, "size": 100},
        {"path": "/x/old.jpg", "modified_date": 1, "size": 100},
    ]
    kept, extras, wasted = t.plan([grp])
    assert kept[0]["path"] == "/x/old.jpg"
    assert [f["path"] for f in extras] == ["/x/a.jpg", "/x/long_name.jpg"]
    assert wasted == 200


def test_report_says_dry_run_and_counts():
    out = t.report(t.parse_groups(load()))
    assert "Exact duplicate groups: 1" in out
    assert "Extra copies: 1" in out
    assert "Nothing was deleted" in out


def test_human_sizes():
    assert t.human(10) == "10 B"
    assert t.human(2048) == "2.0 KB"


def test_cli_from_json_runs():
    r = subprocess.run([sys.executable, os.path.join(HERE, "tidy_dupes.py"), "--from-json", os.path.join(HERE, "sample_dup.json")], capture_output=True, text=True)
    assert r.returncode == 0 and "KEEP" in r.stdout


def test_missing_folder_returns_2():
    assert t.main(["/definitely/not/a/folder"]) == 2


def test_missing_czkawka_returns_3(tmp_path, monkeypatch):
    monkeypatch.setattr(t.shutil, "which", lambda _n: None)
    assert t.main([str(tmp_path)]) == 3


def test_never_calls_delete(monkeypatch):
    src = open(os.path.join(HERE, "tidy_dupes.py"), encoding="utf-8").read()
    assert "os.remove" not in src and "unlink" not in src and "rmtree" not in src and "--delete" not in src


def _fake_exe(tmp_path, body):
    p = tmp_path / "fake_czkawka.py"
    p.write_text("#!/usr/bin/env python3\nimport sys\n" + body)
    p.chmod(0o755)
    return str(p)


def test_run_passes_min_size_flag(tmp_path):
    exe = _fake_exe(tmp_path, "open(sys.argv[sys.argv.index('-p')+1],'w').write('{}')\nassert '-m' in sys.argv and sys.argv[sys.argv.index('-m')+1]=='1'\nsys.exit(11)\n")
    assert t.run_czkawka(str(tmp_path), exe) == {}


def test_exit_zero_means_no_duplicates(tmp_path):
    exe = _fake_exe(tmp_path, "sys.exit(0)\n")
    assert t.run_czkawka(str(tmp_path), exe) == {}


def test_exit_11_without_file_fails_loudly(tmp_path):
    exe = _fake_exe(tmp_path, "sys.exit(11)\n")
    try:
        t.run_czkawka(str(tmp_path), exe)
    except RuntimeError as e:
        assert "not reporting a clean scan" in str(e)
    else:
        raise AssertionError("expected RuntimeError")


def test_other_exit_code_fails_loudly(tmp_path):
    exe = _fake_exe(tmp_path, "sys.stderr.write('boom')\nsys.exit(1)\n")
    assert t.main([str(tmp_path), "--czkawka", exe]) == 4


@pytest.mark.skipif(shutil.which("czkawka_cli") is None, reason="czkawka_cli not installed")
def test_real_czkawka_finds_tiny_duplicates(tmp_path):
    (tmp_path / "a.txt").write_text("hi")
    (tmp_path / "b.txt").write_text("hi")
    data = t.run_czkawka(str(tmp_path), shutil.which("czkawka_cli"))
    assert len(t.parse_groups(data)) == 1
