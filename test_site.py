"""The sha256 published on the page must match the script people download."""
import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).parent


def test_published_sha256_matches_script():
    page = (ROOT / "site" / "index.html").read_text()
    published = re.search(r'id="sha">([0-9a-f]{64})<', page)
    assert published, "page must publish a sha256 for tidy_dupes.py"
    actual = hashlib.sha256((ROOT / "tidy_dupes.py").read_bytes()).hexdigest()
    assert published.group(1) == actual, "update the sha256 in site/index.html"
