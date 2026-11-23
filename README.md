# wowza-dashboard (GENERATED - do not edit by hand)

This repository is the SLIM deployment of the Wowza Streamlit dashboard. It is **generated** from
the v9 production repo (NevixAA/wowza-betting) by `scripts/build_dashboard_repo.py` and pushed as
a whole. Any hand edit here is overwritten by the next build: change the code in v9, then rebuild.

* Code: the dashboard's pages and the modules they import, listed in `deploy/dashboard_manifest.json`.
* Data: NOT in this repo. `dashboard_data/remote_mirror.py` downloads the manifest's data files from
  `https://raw.githubusercontent.com/NevixAA/wowza-betting/main/<path>` into the same relative paths
  at startup and then at most every 10 minutes (the `deploy/SLIM` marker switches it on).
* Built from v9 commit: `a1e459f3f3e0be28c84e1db54bce254f34897428` at 2026-11-23T09:11:46Z. Build id `6cf09f476ef09775`, dashboard schema 1.
* Code/data skew: `deploy/BUILD_INFO.json` records this build; the app compares it with v9's manifest
  at the mirrored data SHA and warns (STALE_BUILD / INCOMPATIBLE / UNKNOWN) when they disagree.

## What the dashboard shows (from the 2026-11-21 go-live)

* **Clean Record first.** Every results figure (Home, Tips, Leagues, Success Rates, Player Props, Overview,
  Model Performance, Clean Record page) counts only tips generated and played on or after the owner's Clean
  Record start (v9 `config.CLEAN_RECORD_START`, 2026-11-21): units (flat 1u), ROI, hit rate, n and a matchday
  block-bootstrap 95% CI. Before the start each reads 0 / "no settled tips yet".
* **Before the repairs** (pre-2026-11-21, old models and the retired Big / Medium / Small gap tiers) is a
  separate, labelled section, for comparison only, never in a Clean Record total. The Clean Record page shows
  both side by side.
* **Bars & Cells**: every league x market cell of the owner-approved bars proposal with its one qualifying
  bar, status (PROVEN / PROMISING / UNPROVEN / WITHDRAWN / OFF) and stake. Staked = a recorded policy stake > 0; every
  other tip is paper.
* Clean retrained team models and clean props models serve from the go-live; there is no global bar and no
  tier on a future tip.

Full instructions: `deploy/README_DASHBOARD_DEPLOY.md`.
