# Lessons log

One row per launch, failed experiment or surprise. Principle, not the example. A repeat becomes a line in CLAUDE.md, a skill, a test or a hook, by a reviewed PR.

| Date | What happened | Evidence | Lesson | Change |
|---|---|---|---|---|
| 2026-10-14 | A page change merged here (#2) did not reach the live site: the deploy reads a second copy in studio-sandbox | This repo's PR #2; sandbox #81; docs/deploy.md | A product with two copies of its deployable files drifts. Deploy from the repo that owns the files, and until then check for drift mechanically | tools/check_deploy_sync.py plus test; workflow move proposed in docs/deploy.md |
