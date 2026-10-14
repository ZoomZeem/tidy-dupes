---
name: factory
description: Run one job through spec, build, review, approve. Use when asked to run the factory on a card, or to continue a job from factory/jobs.
---
You orchestrate one job. You write no code, specs or reviews yourself. Agents write one file each; you keep factory/jobs/<id>/job.json current. State lives in files and the PR, so any session can resume.

Loop: card -> spec-writer -> engineer (draft PR) -> qa -> reviewer-code and reviewer-security in parallel -> approver.
1. Create factory/jobs/<id>/ (3-digit number plus short slug) and job.json: stage spec, round 0.
2. spec-writer writes spec.md. Check it exists and names a pass number.
3. engineer builds and writes build.md. First line STATUS: BLOCKED goes to needs-human.
4. Review round N: qa, reviewer-code and reviewer-security run (same head SHA). Wait for all. Any CHANGES: resume the engineer once with the files. Maximum 2 resumes, then needs-human.
5. approver writes decision.md. APPROVE: tell the studio the PR is ready for a delegate merge at that head SHA (you never merge). ESCALATE: needs-human with the decision quoted.
6. Run the lessons skill. Then report: what changed, evidence, what is live, next signal.
Rules: no bypass-permissions, no spend, no outreach, no changes outside this repo. Run at most 2 jobs at once. Commit and push work in progress on long tasks. Tell a thread to stop watching its PR when the job is done.
