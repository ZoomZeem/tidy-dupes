# Deploy source for https://zoomzeem-tidy.pages.dev/

## Today (14 Oct 2026, verified)
- The page is deployed by `deploy-tidy.yml` in O1ZaemGIT/studio-sandbox. It publishes `apps/tidy/site` to the Cloudflare Pages project `zoomzeem-tidy` on pushes to main that touch `apps/tidy/**`. It copies `apps/tidy/tidy_dupes.py` into the site folder first.
- This repo holds a second copy of the script, tests, sample and page. The two copies drifted once: PR #2 here changed the page and the sandbox copy still deployed the old one until a manual edit (sandbox #81) synced it.
- Until the deploy moves, a change here reaches the live page only after the same change is made in sandbox `apps/tidy`. Run `python3 tools/check_deploy_sync.py <path to studio-sandbox>` after both; it must print `in sync`.

## Proposal: deploy from this repo (needs a workflow, so not done here)
Sessions do not write workflows or secrets. This is the smallest change that leaves one source:
1. Add `.github/workflows/deploy.yml` here: a copy of the sandbox `deploy-tidy.yml` with paths `site/**`, `tidy_dupes.py`, `test_tidy.py`, `test_site.py`; test step `python -m pytest`; stage `cp tidy_dupes.py site/tidy_dupes.py`; deploy `site`. Keep the pinned action SHAs, the pinned wrangler version with its integrity check, the main-only gate and `persist-credentials: false`.
2. Owner action: add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as repo secrets on ZoomZeem/tidy-dupes through the vault (the same free-tier Pages token, scoped to this project if possible). No secret goes in a repo, PR or chat.
3. Order matters: merge and verify the new workflow deploys first, then disable `deploy-tidy.yml` in sandbox and replace `apps/tidy` there with a pointer to this repo. Two workflows must not deploy the same project.
4. After step 3, delete `tools/check_deploy_sync.py` and `test_sync.py`.
Needs a line-by-line reviewer pass (workflow and secrets).
