#!/bin/bash
# Blocks shell commands that break the studio rails. Reads the hook JSON on stdin.
# No jq needed: it matches on the raw JSON text, which errs on the side of blocking.
INPUT=$(cat)
deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}
echo "$INPUT" | grep -qiE 'gh +pr +merge|gh +api[^"]*merge|gh +release|gh +secret|gh +repo +delete' && deny "Blocked: merging, releases and secrets are not for the author. Ask the owner or a reviewer."
echo "$INPUT" | grep -qiE 'git +push[^"]*(-f|--force)' && deny "Blocked: force push."
echo "$INPUT" | grep -qiE 'git +push[^"]*( |:)(main|master)( |"|$)' && deny "Blocked: push to main. Open a draft PR from a branch."
echo "$INPUT" | grep -qiE '(>|tee|sed -i|mv|cp|rm)[^"]*\.github/workflows' && deny "Blocked: workflow files are core and need a real reviewer pass; do not write them from a session."
echo "$INPUT" | grep -qiE 'wrangler|stripe|paypal|--card' && deny "Blocked: anything that could spend money or deploy. No spend without the owner's yes."
exit 0
