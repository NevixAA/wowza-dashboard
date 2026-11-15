# wowza-dashboard (GENERATED - do not edit by hand)

This repository is the SLIM deployment of the Wowza Streamlit dashboard. It is **generated** from
the v9 production repo (NevixAA/wowza-betting) by `scripts/build_dashboard_repo.py` and pushed as
a whole. Any hand edit here is overwritten by the next build: change the code in v9, then rebuild.

* Code: the dashboard's pages and the modules they import, listed in `deploy/dashboard_manifest.json`.
* Data: NOT in this repo. `dashboard_data/remote_mirror.py` downloads the manifest's data files from
  `https://raw.githubusercontent.com/NevixAA/wowza-betting/main/<path>` into the same relative paths
  at startup and then at most every 10 minutes (the `deploy/SLIM` marker switches it on).
* Built from v9 commit: `ab48dec9999240493f739368f462c3629cb11803` at 2026-11-15T10:58:56Z. Build id `64c5b4fde7d3ad6b`, dashboard schema 1.
* Code/data skew: `deploy/BUILD_INFO.json` records this build; the app compares it with v9's manifest
  at the mirrored data SHA and warns (STALE_BUILD / INCOMPATIBLE / UNKNOWN) when they disagree.

Full instructions: `deploy/README_DASHBOARD_DEPLOY.md`.
