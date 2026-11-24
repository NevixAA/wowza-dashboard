#!/usr/bin/env bash
# Build the slim tree from a v9 checkout, mirror it over this repo, commit only when a code or
# manifest file changed, and push - self-healing when main moved under us.
#
#   .github/scripts/sync_from_v9.sh V9_DIR SLIM_DIR BUILD_DIR [MAX_ATTEMPTS]
#
# Used by .github/workflows/sync_from_v9.yml. It lives under .github because the mirror keeps .github
# (rsync --exclude '/.github'), so v9's generator never overwrites it.
#
# Why self-healing: the tree is GENERATED, so a commit that cannot be pushed is never rebased or merged.
# A rebase always conflicts on README.md / deploy/BUILD_INFO.json (both carry a build timestamp), and a
# half-rebase left the 2026-11-24 16:21 run retrying `git pull` on unmerged files until it failed.
# Instead, on a rejected push: abort any rebase, re-fetch main, reset to it, rebuild from the SAME v9
# checkout, re-commit only if a code or manifest file still differs, and push again. Bounded; never forced.
set -euo pipefail

V9_DIR=$(cd "$1" && pwd)
SLIM_DIR=$2
BUILD_DIR=$3
MAX_ATTEMPTS=${4:-5}

cd "$SLIM_DIR"
sha=$(git -C "$V9_DIR" rev-parse --short HEAD)

build_and_mirror() {
  python "$V9_DIR/scripts/build_dashboard_repo.py" "$BUILD_DIR"
  rsync -a --delete --exclude '/.git' --exclude '/.github' "$BUILD_DIR/" ./
}

build_and_mirror
for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  git add -A
  if git diff --cached --quiet -- . ':(exclude)deploy/BUILD_INFO.json' ':(exclude)README.md'; then
    echo "in sync with v9 ${sha} (only build stamps differ) - nothing to commit"
    git reset -q --hard HEAD
    exit 0
  fi
  git diff --cached --stat
  git commit -q -m "Sync from v9 ${sha}: dashboard manifest files"
  if git push origin HEAD:main; then
    echo "pushed v9 ${sha} on attempt ${attempt}"
    exit 0
  fi
  echo "::warning::push attempt ${attempt}/${MAX_ATTEMPTS} rejected (main probably moved)"
  [ "$attempt" -lt "$MAX_ATTEMPTS" ] || break
  echo "resetting to the current main and rebuilding from v9 ${sha}"
  git rebase --abort 2>/dev/null || true
  git merge --abort 2>/dev/null || true
  sleep $((attempt * 5))
  git fetch --depth=1 origin main
  git reset -q --hard FETCH_HEAD
  build_and_mirror
done
echo "::error::could not push the v9 ${sha} sync after ${MAX_ATTEMPTS} attempts"
exit 1
