# tidy-dupes

Find exact duplicate photos in a folder, safely. One command prints which files are byte-for-byte copies, which one it would keep, and how much space the extras use.

It is a **dry run**. It never deletes, moves or renames anything.

Live page: https://zoomzeem-tidy.pages.dev/

```
python3 tidy_dupes.py ~/Pictures
```

Example output:

```
Exact duplicate groups: 1
Extra copies: 1
Space they use: 33.3 KB

KEEP   /photos/a_original.jpg
  copy /photos/a_exact_copy.jpg

Dry run only. Nothing was deleted or moved.
```

## What you need

- Python 3 (tested on 3.12). No extra packages.
- [czkawka_cli](https://github.com/qarmin/czkawka/releases) on your PATH (or pass `--czkawka /path/to/czkawka_cli`). This script is a thin wrapper around it. Download it from the official release page and check the file's sha256 against the one published there before you run it.

## How it works

1. Runs `czkawka_cli dup -s hash -m 1` on your folder. `-m 1` makes it count small files too (Czkawka skips files under 8192 bytes by default). Matching is by file content hash, so a renamed copy is still found.
2. Groups the exact copies. In each group it keeps the oldest-modified file (ties: shortest path) and lists the rest as copies.
3. Prints the report. That is all.

Exit codes of the script: 0 report printed, 2 bad folder, 3 czkawka_cli not found, 4 czkawka_cli failed. If czkawka_cli fails or reports duplicates without writing a result, the script says so and does not print a "clean" report.

Use `--from-json sample_dup.json` to see the report from a saved czkawka result without scanning anything.

## Safety

- The script has no delete or move code. Review the list and remove files yourself.
- "Exact" means the same bytes. Resized, re-saved or edited versions of a photo are not matched.

## Honest limits

- Exact copies only. It does not find "similar" photos.
- Tested on JPEG and BMP files in a small synthetic folder, with czkawka_cli 12.0.2 on Linux. PNG, WebP, Windows and macOS are not verified.
- Empty files are ignored.
- This is an early experiment to see whether anyone wants a safe duplicate finder. It is not a finished product and has no support promise.

## Tests

```
pip install pytest
python -m pytest
```

## Credits

All the duplicate detection is done by [Czkawka](https://github.com/qarmin/czkawka) by Rafał Mikrut and contributors (czkawka_cli is MIT licensed). Czkawka and its authors are not involved with this project.

## License

MIT, see [LICENSE](LICENSE). Copyright (c) 2026 Zoomzeem.
