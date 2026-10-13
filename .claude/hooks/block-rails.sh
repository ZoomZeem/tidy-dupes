#!/bin/bash
# Runs the Python guard. If the guard cannot run or crashes, block (exit 2) rather than allow.
python3 "$(dirname "$0")/block_rails.py" || { echo "Rails guard failed to run; blocking this call. Fix .claude/hooks or ask the owner." >&2; exit 2; }
