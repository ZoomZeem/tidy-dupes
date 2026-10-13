---
name: build-playbook
description: Steps from a studio card to a draft pull request. Use when asked to build or fix something from a card.
---
1. Read the card. Write the test it answers and its pass number first, with the cost (free only).
2. Make the smallest slice that can be run. Add tests.
3. Work on a branch. Run the tests. Open a draft PR that says what changed, what you ran, what you did not run.
4. Ask for a reviewer pass on the head SHA. The author never merges.
5. Core files (pipeline, secrets handling, .github/workflows) need a real reviewer pass, and workflows are not written from a session.
6. Stop and report on captchas, phone or ID signups, paid steps, or anything that would post under the owner's name.
