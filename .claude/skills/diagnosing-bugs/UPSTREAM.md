# Upstream

- Source: https://github.com/mattpocock/skills, `skills/engineering/diagnosing-bugs/SKILL.md`
- Pinned commit: 49dd158d1076134a641b33efb035946536778336 (main on 14 Oct 2026). Not auto-updated. To update, read the new upstream diff and review it like code.
- sha256 of the upstream file at that commit: 849198df88cdb65fd0d97236604c1fca7ff2f22d2f705f9724a800d0266b118d
- Licence: MIT, copied below.

## Changes from upstream (all in SKILL.md)
1. Removed the GLOSSARY.md/ADR line (this repo has neither).
2. Item 10 and the "Agent-runnable" line no longer point at `scripts/hitl-loop.template.sh`, which is not in this repo.
3. Phase 3: the ranked hypotheses go in the PR description or the job's build.md instead of being shown to the user, since studio sessions run unattended.
4. "Ask the user" became "stop and report to the owner".

## Not adopted
`tdd` (same commit, sha256 5505d25b…722e0): overlaps this repo's test-first rule in CLAUDE.md, requires the user to confirm seams before any test (blocks unattended runs), and points at tests.md, mocking.md and two other skills that are not here.

## Licence
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
