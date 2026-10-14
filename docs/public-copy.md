# Public copy checklist (product repos)

Every public surface of a product repo (README, Pages site, social bio) follows these rules before it goes live. The pattern comes from tidy-dupes, the studio's first public experiment.

## Claims

- Say what it does and what it does not do, in the first screen. No adjectives a test cannot back.
- Name what is tested and what is unverified, plainly ("Tested on JPEG and BMP; PNG, WebP, Windows and macOS are not verified").
- If the tool touches user files or data, the safety promise goes up front ("dry run - never deletes, moves or renames") and a test proves it where possible.
- No borrowed credibility: no claims about upstream projects' authors, no implied endorsements.
- Counts carry a date ("As of 14 Oct 2026"). Targets are labeled targets, never measured rates.

## Stage honesty

- A learning prototype says so: "early experiment", no support promise, no feature roadmap implied.
- Internal metrics (pass/fail numbers, visitor targets) stay in internal repos, not in public copy.

## Naming and attribution

- One public name per product, chosen before launch and used everywhere: repo, page URL, package, handle. Record it in the repo. (tidy-dupes shipped with three names - repo, script, page subdomain - and it costs nothing to avoid next time.)
- Attribution line near the top: "An early experiment from ZoomZeem" linking https://github.com/ZoomZeem.

## Before publishing

- Reviewer pass on the copy like code (a README is a public surface).
- Owner approval for anything posted under his name, per the studio rails; org-level surfaces follow D18-D22.
