---
name: review-checklist
description: Checklist for reviewing a studio pull request at its head SHA. Use when asked to review or approve a PR.
---
- Read the head SHA, not the description. Say which SHA you read.
- Does the code do what the PR claims? Are the tests real and do they fail without the change?
- Safety: no secrets, no deletes of user files, no spend, no paid service, nothing posted in the owner's name.
- Core files (pipeline, secrets handling, .github/workflows): read every line. A skim is not a pass.
- Honesty: README and page claims match what was actually tested.
- Verdict: PASS or CHANGES, with the SHA. The reviewer never edits the PR.
