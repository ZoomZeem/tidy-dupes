#!/usr/bin/env python3
"""Dry-run exact-duplicate photo report using czkawka_cli. Never deletes or moves anything."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

INSTALL_HELP = (
    "czkawka_cli was not found on PATH.\n"
    "Get it from https://github.com/qarmin/czkawka/releases (check the sha256 on the release page),\n"
    "or on Windows: winget install czkawka  (check the package name with: winget search czkawka)."
)


def parse_groups(data):
    """czkawka dup JSON: {size: [[file, file, ...], ...]} -> list of groups, each a list of file dicts."""
    groups = []
    for _size, size_groups in data.items():
        for grp in size_groups:
            if len(grp) >= 2:
                groups.append(grp)
    return groups


def plan(groups):
    """Keep the oldest-modified, then shortest path, in each group. Returns (kept, extras, bytes_wasted)."""
    kept, extras, wasted = [], [], 0
    for grp in groups:
        ordered = sorted(grp, key=lambda f: (f.get("modified_date", 0), len(f["path"]), f["path"]))
        kept.append(ordered[0])
        for f in ordered[1:]:
            extras.append(f)
            wasted += int(f.get("size", 0))
    return kept, extras, wasted


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def report(groups):
    kept, extras, wasted = plan(groups)
    lines = [f"Exact duplicate groups: {len(groups)}", f"Extra copies: {len(extras)}", f"Space they use: {human(wasted)}", ""]
    for grp in groups:
        ordered = sorted(grp, key=lambda f: (f.get("modified_date", 0), len(f["path"]), f["path"]))
        lines.append(f"KEEP   {ordered[0]['path']}")
        for f in ordered[1:]:
            lines.append(f"  copy {f['path']}")
        lines.append("")
    lines.append("Dry run only. Nothing was deleted or moved.")
    return "\n".join(lines)


def run_czkawka(folder, exe):
    """Run czkawka_cli. Exit 0 = nothing found, 11 = duplicates found (verified on 12.0.2). Anything else fails loudly."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "dup.json")
        # -m 1: czkawka skips files under 8192 bytes by default; count every non-empty file.
        proc = subprocess.run([exe, "dup", "-d", folder, "-s", "hash", "-m", "1", "-p", out], capture_output=True, text=True)
        if proc.returncode == 0:
            return {}
        if proc.returncode != 11:
            raise RuntimeError(f"czkawka_cli failed ({proc.returncode}): {proc.stderr.strip()[:300]}")
        if not os.path.exists(out):
            raise RuntimeError("czkawka_cli reported duplicates (exit 11) but wrote no result file; not reporting a clean scan.")
        with open(out, encoding="utf-8") as fh:
            return json.load(fh)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Dry-run exact-duplicate photo report (never deletes).")
    ap.add_argument("folder", nargs="?", help="folder to scan")
    ap.add_argument("--from-json", help="read an existing czkawka dup JSON instead of scanning")
    ap.add_argument("--czkawka", default=None, help="path to czkawka_cli (default: look on PATH)")
    args = ap.parse_args(argv)
    if args.from_json:
        with open(args.from_json, encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        if not args.folder or not os.path.isdir(args.folder):
            print("Give an existing folder to scan.", file=sys.stderr)
            return 2
        exe = args.czkawka or shutil.which("czkawka_cli")
        if not exe:
            print(INSTALL_HELP, file=sys.stderr)
            return 3
        try:
            data = run_czkawka(args.folder, exe)
        except RuntimeError as err:
            print(f"Error: {err}", file=sys.stderr)
            return 4
    print(report(parse_groups(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
