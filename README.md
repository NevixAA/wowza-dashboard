# wowza-dashboard (GENERATED - do not edit by hand)

This repository is the SLIM deployment of the Wowza Streamlit dashboard. It is **generated** from
the v9 production repo (NevixAA/wowza-betting) by `scripts/build_dashboard_repo.py` and pushed as
a whole. Any hand edit here is overwritten by the next build: change the code in v9, then rebuild.

* Code: the dashboard's pages and the modules they import, listed in `deploy/dashboard_manifest.json`.
* Data: NOT in this repo. `dashboard_data/remote_mirror.py` downloads the manifest's data files from
  `https://raw.githubusercontent.com/NevixAA/wowza-betting/main/<path>` into the same relative paths
  at startup and then at most every 10 minutes (the `deploy/SLIM` marker switches it on).
* Built from v9 commit: `f5e3e9fcdb83aad70993c527106d2e5df26d23e1` at 2026-11-18T17:33:50Z. Build id `d2566776576f893d`, dashboard schema 1.
* Code/data skew: `deploy/BUILD_INFO.json` records this build; the app compares it with v9's manifest
  at the mirrored data SHA and warns (STALE_BUILD / INCOMPATIBLE / UNKNOWN) when they disagree.

Full instructions: `deploy/README_DASHBOARD_DEPLOY.md`.
