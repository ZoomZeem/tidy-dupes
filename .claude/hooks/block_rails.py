#!/usr/bin/env python3
"""PreToolUse guard for the studio rails. Reads the hook JSON on stdin.

Best effort, not a sandbox. It parses the shell command (not a raw text match) and denies:
pushes without an explicit non-default destination, merges, releases and secrets via gh,
commits on main, writes to workflow files and to this guard's own files, any touch of
secret files, and deploy or payment tools. It cannot see what a script it did not parse
does at run time (python script.py, make, npm run). Server-side controls are the real rail:
see CLAUDE.md.
"""
import json
import os
import re
import shlex
import subprocess
import sys

DEFAULT_BRANCHES = {"main", "master"}
READ_ONLY = {"cat", "ls", "head", "tail", "grep", "rg", "less", "more", "wc", "diff", "find", "stat", "file", "tree"}
GIT_READ_ONLY = {"diff", "log", "show", "status", "blame", "ls-files", "grep", "cat-file", "rev-parse", "branch", "remote", "fetch", "config"}
WRAPPERS = {"env", "sudo", "command", "nohup", "time", "exec", "nice", "timeout", "xargs", "stdbuf"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
INLINE = {"python", "python3", "node", "perl", "ruby", "php", "deno", "bun"}
DENY_TOOLS = {"wrangler", "stripe", "paypal"}


class Deny(Exception):
    pass


def norm(path):
    p = path.replace("\\", "/")
    p = re.sub(r"/+", "/", p)
    parts = []
    for part in p.split("/"):
        if part in ("", "."):
            continue
        if part == ".." and parts and parts[-1] != "..":
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


def is_secret(path):
    p = norm(path)
    base = p.rsplit("/", 1)[-1].lower()
    comps = [c.lower() for c in p.split("/")]
    if base in (".env.example", ".env.sample", ".env.template"):
        return False
    return (
        base == ".env" or base.startswith(".env.") or base.endswith(".pem") or base.endswith(".key")
        or base.startswith("id_rsa") or base.startswith("id_ed25519") or base in ("credentials", ".npmrc", ".netrc", ".pypirc")
        or any(c in ("secrets", "secret", ".aws", ".ssh", ".gnupg") for c in comps)
    )


def is_write_protected(path):
    p = "/" + norm(path)
    return (
        "/.github/workflows" in p + "/"
        or "/.claude/settings" in p
        or "/.claude/hooks" in p + "/"
        or p.endswith("/.claude/hooks")
    )


PARENTS = (".claude", ".github")


def is_protected_parent(path):
    p = norm(path)
    return p.rsplit("/", 1)[-1] in PARENTS or p in ("", "..") or p.endswith("/..")


def current_branch(cwd):
    try:
        out = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip()
    except Exception:
        return ""


def split_segments(cmd):
    # split on ; && || | & and newlines, outside quotes
    segs, buf, q, i = [], "", None, 0
    while i < len(cmd):
        c = cmd[i]
        if q:
            buf += c
            if c == q and (q == "'" or cmd[i - 1] != "\\"):
                q = None
        elif c in "'\"":
            q = c
            buf += c
        elif c == "\\" and i + 1 < len(cmd):
            buf += c + cmd[i + 1]
            i += 1
        elif c in ";\n|&":
            if buf.strip():
                segs.append(buf)
            buf = ""
        else:
            buf += c
        i += 1
    if buf.strip():
        segs.append(buf)
    return segs


def substitutions(cmd):
    subs = re.findall(r"\$\(([^()]*)\)", cmd) + re.findall(r"`([^`]*)`", cmd)
    return subs


def tokens_of(seg):
    lex = shlex.shlex(seg, posix=True, punctuation_chars="<>")
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def check_paths(tokens, writing):
    """Deny any token that is a protected path, honouring read-only commands for workflows."""
    for t in tokens:
        if t.startswith("-") and "=" in t:
            t = t.split("=", 1)[1]
        if is_secret(t):
            raise Deny("secret and env files are off limits (read, write or stage)")
        if writing and is_write_protected(t):
            raise Deny("workflow files and the guard's own files need a real reviewer pass; do not write them from a session")
        if writing and is_protected_parent(t) and not t.startswith("-"):
            raise Deny("this path is, or contains, workflow or guard files; do not remove, move or overwrite it from a session")


def check_git(args, cwd):
    i, c = 0, cwd
    while i < len(args):
        a = args[i]
        if a == "-C" and i + 1 < len(args):
            c = args[i + 1]
            i += 2
        elif a in ("-c", "--git-dir", "--work-tree", "--namespace", "--exec-path") and i + 1 < len(args):
            if a == "--work-tree":
                c = args[i + 1]
            i += 2
        elif a.startswith("-"):
            i += 1
        else:
            break
    if i >= len(args):
        return
    sub, rest = args[i], args[i + 1:]
    if sub == "push":
        flags = [a for a in rest if a.startswith("-")]
        pos = [a for a in rest if not a.startswith("-")]
        bad = {"-f", "--force", "--force-with-lease", "--mirror", "--all", "--delete", "-d", "--tags", "--prune"}
        for f in flags:
            if f in bad or f.startswith("--force-with-lease=") or f.startswith("--force-if-includes"):
                raise Deny("force, mirror, all, delete, prune or tags push")
            if re.fullmatch(r"-[a-zA-Z]*[fd][a-zA-Z]*", f) and not f.startswith("--"):
                raise Deny("force or delete push flag")
        if len(pos) < 2:
            raise Deny("name the destination branch explicitly, for example: git push -u origin my-branch")
        for ref in pos[1:]:
            if ref.startswith("+"):
                raise Deny("force refspec")
            if ref.startswith(":"):
                raise Deny("deleting a remote branch")
            if any(ch in ref for ch in "*?[{"):
                raise Deny("glob refspec can include the default branch")
            src, _, dst = ref.partition(":")
            dest = dst if ":" in ref else src
            dest = re.sub(r"^refs/heads/", "", dest)
            if dest == "" or dest in DEFAULT_BRANCHES or dest == "HEAD" or dest.startswith("refs/") and not dest.startswith("refs/heads/"):
                raise Deny("push to main, master, HEAD, a delete or a non-branch ref. Open a draft PR from a branch")
        return
    if sub in ("commit", "merge", "rebase", "cherry-pick", "pull", "revert", "am"):
        if current_branch(c) in DEFAULT_BRANCHES:
            raise Deny("you are on the default branch; create a branch first")
    if sub in ("update-ref", "filter-branch", "filter-repo"):
        raise Deny("history and ref rewriting is not allowed")
    if sub == "branch" and any(a in ("-f", "-D", "--force", "-M") for a in rest) and any(a in DEFAULT_BRANCHES for a in rest):
        raise Deny("do not move or delete the default branch")
    if sub in ("commit", "tag", "notes"):
        return  # message text is not a path
    writing = sub not in GIT_READ_ONLY
    check_paths(rest, writing)


def check_gh(args):
    pos, i = [], 0
    while i < len(args):
        a = args[i]
        if a in ("-R", "--repo", "--hostname"):
            i += 2
            continue
        if not a.startswith("-"):
            pos.append(a)
        i += 1
    if not pos:
        return
    top = pos[0]
    sub = pos[1] if len(pos) > 1 else ""
    if top in ("release", "secret", "workflow", "ruleset") or (top == "repo" and sub in ("delete", "edit", "archive", "rename", "transfer")):
        raise Deny("gh " + top + " is not for the author")
    if top == "pr" and sub in ("merge", "ready", "close", "reopen", "edit") and sub == "merge":
        raise Deny("merging is not for the author")
    if top == "pr" and sub == "review" and any(a in ("--approve", "-a") for a in args):
        raise Deny("the author does not approve their own PR")
    if top == "api":
        method = "GET"
        field = False
        for j, a in enumerate(args):
            if a in ("-X", "--method") and j + 1 < len(args):
                method = args[j + 1].upper()
            if a.startswith("--method="):
                method = a.split("=", 1)[1].upper()
            if a.startswith("-X") and len(a) > 2:
                method = a[2:].upper()
            if re.match(r"^(-f|-F)", a) or a.startswith(("--field", "--raw-field", "--input")):
                field = True
        if method != "GET" or field or "merge" in " ".join(args):
            raise Deny("gh api with a write method, field options or a merge call")


def check_simple(tokens, cwd, depth=0):
    if depth > 4:
        raise Deny("command nesting too deep to check")
    # redirections
    for j, t in enumerate(tokens):
        if t and set(t) <= set("<>") and ">" in t and j + 1 < len(tokens):
            check_paths([tokens[j + 1]], True)
    toks = [t for t in tokens if not (t and set(t) <= set("<>"))]
    # drop env assignments and wrappers
    while toks and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]) or os.path.basename(toks[0]) in WRAPPERS):
        toks = toks[1:]
        while toks and toks[0].startswith("-") and len(toks) > 1:
            toks = toks[1:]
    if not toks:
        return
    prog = os.path.basename(toks[0])
    args = toks[1:]
    if prog in ("eval", "source", ".") or prog in DENY_TOOLS or any(os.path.basename(a) in DENY_TOOLS for a in args[:2]) and prog in ("npx", "bunx", "pnpx", "yarn", "npm", "pnpm"):
        raise Deny("eval, deploy and payment tools are blocked. No spend without the owner's yes")
    if "--card" in toks:
        raise Deny("payment flags are blocked")
    if prog in SHELLS and "-c" in args:
        k = args.index("-c")
        if k + 1 < len(args):
            check_command(args[k + 1], cwd, depth + 1)
        return
    if prog in INLINE and any(a in ("-c", "-e", "--eval", "-p", "-r") for a in args):
        code = " ".join(args)
        if re.search(r"\.env|\.pem|id_rsa|id_ed25519|credentials|\.npmrc|\.netrc|\.aws|\.ssh|secrets?\b|\.github/+workflows|\.claude/+(settings|hooks)", code):
            raise Deny("inline code that names secret, workflow or guard files")
    if prog in ("cd", "pushd", "chdir"):
        for a in args:
            if not a.startswith("-") and (is_protected_parent(a) or is_write_protected(a) or is_secret(a)):
                raise Deny("do not change into workflow, guard or secret directories")
    if prog == "git":
        check_git(args, cwd)
    elif prog == "gh":
        check_gh(args)
    else:
        read_only = prog in READ_ONLY
        if prog == "find" and any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0", "-fprintf", "-fls") for a in args):
            read_only = False
        if prog == "rm" and any(re.fullmatch(r"-[a-zA-Z]*[rR][a-zA-Z]*|--recursive", a) for a in args) and any(a in (".", "..", "/", "~", "*", "./", "../", "./*", "../*", "/*") for a in args):
            raise Deny("recursive remove of a broad path")
        check_paths(args, not read_only)


def check_command(cmd, cwd, depth=0):
    for sub in substitutions(cmd):
        check_command(sub, cwd, depth + 1)
    for seg in split_segments(cmd):
        try:
            toks = tokens_of(seg)
        except ValueError:
            raise Deny("could not parse this command safely")
        if toks:
            check_simple(toks, cwd, depth)


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "Blocked: " + reason}}))
    sys.exit(0)


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    try:
        if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            path = ti.get("file_path") or ti.get("notebook_path") or ""
            check_paths([path], True)
        elif tool in ("Read",):
            check_paths([ti.get("file_path", "")], False)
        else:
            check_command(ti.get("command", ""), cwd)
    except Deny as e:
        deny(str(e))


if __name__ == "__main__":
    main()
