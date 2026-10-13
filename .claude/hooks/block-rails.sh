#!/bin/bash
# Blocks shell commands that break the studio rails. Reads the hook JSON on stdin.
# No jq needed: it matches on the raw JSON text, which errs on the side of blocking.
# Quotes inside the command arrive escaped in the JSON, so patterns use .* not [^"]*.
INPUT=$(cat)
deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}
has() { printf '%s' "$INPUT" | grep -qiE "$1"; }

# 1. Merging, releases, secrets, deletes of repos.
has 'gh +pr +merge|gh +api.*merge|gh +release|gh +secret|gh +repo +delete' && deny "Blocked: merging, releases and secrets are not for the author. Ask the owner or a reviewer."

# 2. Pushes. Only an explicit non-default branch is allowed.
if has 'git +(-C +[^ ]+ +)?push'; then
  has 'git +(-C +[^ ]+ +)?push.*(-f|--force|--mirror|--all|--delete|--tags)' && deny "Blocked: force, mirror, all, delete or tags push."
  has 'git +(-C +[^ ]+ +)?push.*[ :\\"/](main|master)( |:|\\"|"|$)' && deny "Blocked: push to main or master. Open a draft PR from a branch."
  # Bare push, or push with only flags and a remote, goes to the current or default branch.
  has 'git +(-C +[^ ]+ +)?push( +(-u|--set-upstream|--no-verify))*( +[A-Za-z0-9_.-]+)? *(\\"|"|;|&|\||$)' && deny "Blocked: name the branch explicitly, for example: git push -u origin my-branch."
  has 'git +(-C +[^ ]+ +)?push.* HEAD( |\\"|"|$)' && deny "Blocked: push HEAD without a branch name. Use HEAD:my-branch or the branch name."
  BR=$(git -C "${CLAUDE_PROJECT_DIR:-.}" rev-parse --abbrev-ref HEAD 2>/dev/null)
  case "$BR" in main|master) deny "Blocked: you are on $BR. Create a branch first.";; esac
fi
# Commits on main or master are blocked too.
if has 'git +(-C +[^ ]+ +)?commit'; then
  BR=$(git -C "${CLAUDE_PROJECT_DIR:-.}" rev-parse --abbrev-ref HEAD 2>/dev/null)
  case "$BR" in main|master) deny "Blocked: commit on $BR. Create a branch first.";; esac
fi

# 3. Workflow files: no writing from a session, however the path is quoted.
has '\.github/+workflows' && has '(>|tee |sed +-i|mv |cp |rm |touch |python|node |perl |ruby |install |dd |truncate|git +(add|apply|checkout|restore|rm|mv)|ed |awk .*-i)' && deny "Blocked: workflow files are core and need a real reviewer pass; do not write them from a session."

# 4. Secret files: no writing, no reading, no staging.
SECRET='(^|[^A-Za-z0-9])\.env([^A-Za-z0-9]|$)|\.env\.|\.pem|id_rsa|id_ed25519|credentials|\.npmrc|\.netrc|secrets?(\.|/|[^A-Za-z0-9])|\.aws/|\.ssh/'
has "$SECRET" && has '(>|tee |sed |mv |cp |rm |touch |cat |less |more |head |tail |grep |rg |awk |base64|xxd|od |strings|python|node |perl |curl|wget|scp |git +(add|apply|checkout|restore|rm|mv))' && deny "Blocked: secret and env files are off limits (read, write or stage)."

# 5. Anything that could spend money or deploy.
has 'wrangler|stripe|paypal|--card' && deny "Blocked: anything that could spend money or deploy. No spend without the owner's yes."
exit 0
