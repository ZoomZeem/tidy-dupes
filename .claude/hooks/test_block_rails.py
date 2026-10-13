"""Tests for block_rails.py. Run: python -m pytest .claude/hooks"""
import json
import os
import subprocess

import pytest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block_rails.py")

BASH = [
    # pushes
    ("git push origin main", "feat", "deny"),
    ("git push origin feat", "feat", "allow"),
    ("git push -u origin my-branch", "feat", "allow"),
    ("git push origin bug-fix", "feat", "allow"),
    ("git push -u origin fix-docs-d", "feat", "allow"),
    ("git push", "feat", "deny"),
    ("git push origin", "feat", "deny"),
    ("git push -u origin", "feat", "deny"),
    ("git push origin HEAD", "feat", "deny"),
    ("git push origin HEAD:feat", "feat", "allow"),
    ("git push origin HEAD:main", "feat", "deny"),
    ("git push origin HEAD:refs/heads/main", "feat", "deny"),
    ("git push origin feat:refs/heads/master", "feat", "deny"),
    ("git push origin feat", "main", "allow"),
    ("git push origin :feat", "feat", "deny"),
    ("git push origin +feat", "feat", "deny"),
    ("git push --force origin feat", "feat", "deny"),
    ("git push -f origin feat", "feat", "deny"),
    ("git push --force-with-lease origin feat", "feat", "deny"),
    ("git push origin feat --tags", "feat", "deny"),
    ("git -C /x push", "feat", "deny"),
    ("git -C /x push origin main", "feat", "deny"),
    ("git -c core.x=1 push origin main", "feat", "deny"),
    ("git status && git push origin main", "feat", "deny"),
    ("echo ok; git push", "feat", "deny"),
    ("bash -c 'git push origin main'", "feat", "deny"),
    ("echo $(git push origin main)", "feat", "deny"),
    ("FOO=1 git push origin main", "feat", "deny"),
    # commits and history
    ("git commit -m x", "main", "deny"),
    ("git commit -m x", "feat", "allow"),
    ("git commit -m 'note about secrets/ docs'", "feat", "allow"),
    ("git merge feat", "main", "deny"),
    ("git checkout -b x", "main", "allow"),
    ("git update-ref refs/heads/main abc", "feat", "deny"),
    # gh
    ("gh pr merge 5", "feat", "deny"),
    ("gh -R org/repo pr merge 5", "feat", "deny"),
    ("gh pr merge --squash 5 -R org/repo", "feat", "deny"),
    ("gh pr create --draft", "feat", "allow"),
    ("gh pr view 5", "feat", "allow"),
    ("gh pr review 5 --approve", "feat", "deny"),
    ("gh release create v1", "feat", "deny"),
    ("gh secret set X", "feat", "deny"),
    ("gh api -X PUT repos/o/r/pulls/5/merge", "feat", "deny"),
    ("gh api repos/o/r/pulls/5", "feat", "allow"),
    ("gh workflow run x.yml", "feat", "deny"),
    # workflows and guard files
    ("echo hi > .github/workflows/a.yml", "feat", "deny"),
    ('echo hi > ".github/workflows/a.yml"', "feat", "deny"),
    ("echo hi >> './.github/workflows/a.yml'", "feat", "deny"),
    ("echo hi > ../repo/.github/workflows/a.yml", "feat", "deny"),
    ("sed -i s/a/b/ '.github/workflows/ci.yml'", "feat", "deny"),
    ("tee .github/workflows/x.yml", "feat", "deny"),
    ("cp x .github//workflows/y.yml", "feat", "deny"),
    ("git add .github/workflows/ci.yml", "feat", "deny"),
    ("python3 -c \"open('.github/workflows/x.yml','w')\"", "feat", "deny"),
    ("cat .github/workflows/ci.yml", "feat", "allow"),
    ("ls .github/workflows", "feat", "allow"),
    ("git diff .github/workflows", "feat", "allow"),
    ("echo x > .claude/settings.json", "feat", "deny"),
    ("sed -i s/a/b/ .claude/hooks/block_rails.py", "feat", "deny"),
    ("rm .claude/hooks/block_rails.py", "feat", "deny"),
    ("cat .claude/settings.json", "feat", "allow"),
    # secrets
    ("echo KEY=1 > .env", "feat", "deny"),
    ('echo KEY=1 >> ".env.local"', "feat", "deny"),
    ("cat .env", "feat", "deny"),
    ("cat .env.example", "feat", "allow"),
    ("cp x ~/.ssh/id_rsa", "feat", "deny"),
    ("git add .env", "feat", "deny"),
    ("echo x > secrets/a.txt", "feat", "deny"),
    ("cat ~/.aws/credentials", "feat", "deny"),
    ("grep KEY config/.env.production", "feat", "deny"),
    # money and deploy
    ("npx wrangler deploy", "feat", "deny"),
    ("wrangler pages deploy x", "feat", "deny"),
    # ordinary work
    ("pytest -q", "feat", "allow"),
    ("python3 -m pytest", "feat", "allow"),
    ("git status", "feat", "allow"),
    ("ls environment", "feat", "allow"),
    ("git log --oneline | head", "feat", "allow"),
    ("echo done 2>&1", "feat", "allow"),
]

TOOLS = [
    ("Edit", {"file_path": ".github/workflows/ci.yml"}, "deny"),
    ("Write", {"file_path": "/repo/.claude/settings.json"}, "deny"),
    ("Edit", {"file_path": ".claude/hooks/block_rails.py"}, "deny"),
    ("Write", {"file_path": "app/.env"}, "deny"),
    ("Read", {"file_path": "app/.env"}, "deny"),
    ("Read", {"file_path": ".github/workflows/ci.yml"}, "allow"),
    ("Edit", {"file_path": "apps/tidy/tidy_dupes.py"}, "allow"),
]


@pytest.fixture()
def repo(tmp_path):
    def sh(cmd):
        subprocess.run(cmd, shell=True, cwd=tmp_path, check=True, capture_output=True)
    sh("git init -q -b main && git -c user.email=a@b -c user.name=x commit -q --allow-empty -m init")
    return tmp_path, sh


def run(path, payload):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(path))
    out = subprocess.run(["python3", HOOK], input=json.dumps(payload), capture_output=True, text=True, env=env)
    assert out.returncode == 0, out.stderr
    if out.stdout.strip():
        data = json.loads(out.stdout)  # a deny must be valid JSON
        assert data["hookSpecificOutput"]["permissionDecision"] == "deny"
        return "deny"
    return "allow"


@pytest.mark.parametrize("command,branch,expected", BASH)
def test_bash(repo, command, branch, expected):
    path, sh = repo
    sh(f"git checkout -q -B {branch}")
    assert run(path, {"tool_name": "Bash", "tool_input": {"command": command}}) == expected, command


@pytest.mark.parametrize("tool,tool_input,expected", TOOLS)
def test_file_tools(repo, tool, tool_input, expected):
    path, _ = repo
    assert run(path, {"tool_name": tool, "tool_input": tool_input}) == expected
