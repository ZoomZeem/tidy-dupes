"""Compare this repo with the studio-sandbox copy that deploys the page.

Usage: python3 tools/check_deploy_sync.py /path/to/studio-sandbox
Exit 0 if the files match, 1 if any differ or are missing, 2 on bad usage.
Until the deploy moves into this repo (docs/deploy.md), run this before and
after any change to tidy_dupes.py or site/.
"""
import hashlib
import pathlib
import sys

# (file here, file under apps/tidy in studio-sandbox)
PAIRS = [
    ("tidy_dupes.py", "tidy_dupes.py"),
    ("test_tidy.py", "test_tidy.py"),
    ("sample_dup.json", "sample_dup.json"),
    ("site/index.html", "site/index.html"),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def compare(here, sandbox):
    """Return a list of problems; empty means in sync."""
    problems = []
    for mine, theirs in PAIRS:
        a, b = digest(here / mine), digest(sandbox / "apps" / "tidy" / theirs)
        if a is None or b is None:
            problems.append(f"missing: {mine} ({'here' if a is None else 'sandbox'})")
        elif a != b:
            problems.append(f"differs: {mine}")
    return problems


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    problems = compare(pathlib.Path(__file__).resolve().parent.parent, pathlib.Path(argv[1]))
    for p in problems:
        print(p)
    print("in sync" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
