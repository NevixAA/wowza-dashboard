"""One switch for every read of Pro's outputs (owner 2026-11-28).

GitHub blocked NevixAA/wowzaV9-Pro on 2026-11-27 (every API and git access: 403 "Repository access blocked").
Pro's collectors now run on the owner's server, which publishes a curated set of Pro OUTPUTS to the PRIVATE
repo NevixAA/wowza-exec, branch pro-outputs (server job pro_publish, /srv/wowza/bin/pro_publish.py), with a
manifest pro_outputs_manifest.json (produced_at, source commits, sha256 per file, per group PUBLISHED or
WITHHELD + as_of = when its producer job last finished OK on the server).

Two repository variables, passed to the workflows as env vars:

    PRO_SOURCE unset / empty / github  -> the GitHub repo, governed by PRO_REPO_AVAILABLE (behaviour before)
        PRO_REPO_AVAILABLE unset / anything else -> available
        PRO_REPO_AVAILABLE = 0 | false | no | off -> unavailable (source blocked)
    PRO_SOURCE = exec                  -> the server copy: a checkout of wowza-exec@pro-outputs at PRO_EXEC_DIR
                                          (scripts/pro_outputs_fetch.sh, read-only key PRICE_STORE_RO_KEY). Each
                                          read checks the manifest: missing, stale (produced_at or the group's
                                          as_of older than the reader's limit), WITHHELD or not listed ->
                                          UNAVAILABLE with the reason. Never read from GitHub or a stale copy.
    PRO_SOURCE = none                  -> unavailable, nothing is read
    PRO_SOURCE = anything else         -> unavailable (unknown value: fail closed)

Unavailable means: every Pro source is skipped with a notice, and each output that uses Pro data shows it as
UNAVAILABLE - never stale data as current, never invented data, never a silent pass.

scripts/price_store_sync.py runs from a sparse checkout without src/ and carries the same rule inline.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ENV = "PRO_REPO_AVAILABLE"
SOURCE_ENV = "PRO_SOURCE"
EXEC_DIR_ENV = "PRO_EXEC_DIR"
REPO = "NevixAA/wowzaV9-Pro"
EXEC_REPO = "NevixAA/wowza-exec"
EXEC_BRANCH = "pro-outputs"
MANIFEST = "pro_outputs_manifest.json"
EXEC_LABEL = "server via exec"
OFF = {"0", "false", "no", "off"}
SOURCES = ("github", "exec", "none")
REASON = f"source blocked: {REPO} is unavailable ({ENV}=0)"
#: produced_at older than this -> the whole server copy is stale (the server publishes every 30 min and
#: commits at least every 2 h). A reader passes its own limit for the group's as_of.
MANIFEST_MAX_AGE_H = 6.0
ROOT = Path(__file__).resolve().parents[1]


def source(value: str | None = None) -> str:
    """github | exec | none | unknown. Unset/empty = github (behaviour before the switch)."""
    v = ((os.getenv(SOURCE_ENV) if value is None else value) or "").strip().lower()
    if not v:
        return "github"
    return v if v in SOURCES else "unknown"


def exec_dir() -> Path:
    return Path(os.getenv(EXEC_DIR_ENV) or (ROOT.parent / "pro-outputs"))


def _ts(v) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _age_h(v, now: datetime) -> float | None:
    t = _ts(v)
    return None if t is None else (now - t).total_seconds() / 3600


def manifest(root: Path | None = None) -> dict | None:
    try:
        d = json.loads((Path(root or exec_dir()) / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def group_of(man: dict, rel: str) -> str | None:
    """The manifest group a published file, or a directory / file named in a group's paths, belongs to."""
    f = (man.get("files") or {}).get(rel)
    if f:
        return f.get("group")
    r = rel.rstrip("/")
    for name, g in (man.get("groups") or {}).items():
        for p in g.get("paths") or []:
            if r == p.rstrip("/") or (p.endswith("/") and r.startswith(p)):
                return name
    return None


def exec_status(rel: str | None = None, max_age_hours: float | None = None, *, root: Path | None = None,
                now: datetime | None = None, man: dict | None = None) -> tuple[bool, str, dict]:
    """(ok, reason, info) for the server copy as a whole, or for one file / directory in it.

    info: produced_at, and for a path its group and the group's as_of. ok=False always carries a reason;
    nothing is ever assumed fresh. man: an already-read manifest (the dashboard fetches it over the API); then the
    file itself is not looked for on disk."""
    now = now or datetime.now(timezone.utc)
    on_disk = man is None
    man = manifest(root) if on_disk else man
    if man is None:
        return False, f"Pro server copy not read ({EXEC_REPO}@{EXEC_BRANCH} not fetched this run)", {}
    info = {"produced_at": man.get("produced_at")}
    age = _age_h(man.get("produced_at"), now)
    if age is None:
        return False, "Pro server copy has no produced_at", info
    if age > MANIFEST_MAX_AGE_H:
        return False, (f"Pro server copy is stale: produced_at {man.get('produced_at')} ({age:.1f} h ago, "
                       f"limit {MANIFEST_MAX_AGE_H:g} h)"), info
    if rel is None:
        return True, "", info
    g = group_of(man, rel)
    grp = (man.get("groups") or {}).get(g) if g else None
    info.update(group=g, as_of=(grp or {}).get("as_of"))
    if grp is None:
        return False, f"{rel} is not published by the Pro server", info
    if grp.get("status") != "PUBLISHED":
        return False, f"{rel} withheld by the Pro server: {grp.get('reason') or 'no reason given'}", info
    limit = float(max_age_hours if max_age_hours is not None else grp.get("max_age_hours") or MANIFEST_MAX_AGE_H)
    gage = _age_h(grp.get("as_of"), now)
    if gage is None or gage > limit:
        return False, (f"{rel} on the Pro server is stale: as_of {grp.get('as_of')} "
                       f"({'unknown age' if gage is None else f'{gage:.1f} h ago'}, limit {limit:g} h)"), info
    if on_disk and not (Path(root or exec_dir()) / rel).exists():
        return False, f"{rel} listed but absent from the Pro server copy", info
    return True, "", info


def available(value: str | None = None) -> bool:
    """Pro may be read at all. github: False only when PRO_REPO_AVAILABLE is explicitly off (unset = available).
    exec: the server copy is fetched and its manifest is fresh. none / unknown: False."""
    s = source()
    if s == "github":
        v = os.getenv(ENV) if value is None else value
        return (v or "").strip().lower() not in OFF
    if s == "exec":
        return exec_status()[0]
    return False


def reason() -> str:
    """Why Pro is unavailable right now ('' when it is available)."""
    s = source()
    if s == "github":
        return "" if available() else REASON
    if s == "exec":
        return exec_status()[1]
    if s == "none":
        return f"Pro source switched off ({SOURCE_ENV}=none)"
    return f"unknown {SOURCE_ENV} value - fail closed"


def label() -> str:
    """Where Pro is read from, for records (predictions_sources.json, logs)."""
    return {"github": f"GitHub {REPO}", "exec": EXEC_LABEL}.get(source(), "not read")


def exec_path(rel: str, max_age_hours: float | None = None, what: str | None = None) -> Path | None:
    """The server-copy path of one Pro output when it may be read, else None (with a notice saying why)."""
    ok, why, _ = exec_status(rel, max_age_hours)
    if ok:
        return exec_dir() / rel
    notice(what or rel, why)
    return None


def locate(rel: str, legacy_bases=(), max_age_hours: float | None = None, what: str | None = None):
    """Where a reader finds one Pro output.

    -> ("path", Path)    read this local file
    -> ("legacy", None)  github mode, not found locally: the reader may try its GitHub fallback as before
    -> ("none", None)    unavailable (a notice was printed): read nothing, show it as missing
    exec mode reads ONLY the server copy; github mode keeps the old order (sibling checkouts, then GitHub)."""
    if source() == "exec":
        p = exec_path(rel, max_age_hours, what)
        return ("path", p) if p is not None else ("none", None)
    if not available():
        notice(what or rel)
        return "none", None
    for b in legacy_bases:
        if b and os.path.exists(os.path.join(b, rel)):
            return "path", Path(b) / rel
    return "legacy", None


def notice(what: str, why: str | None = None) -> str:
    """One GitHub Actions notice line for a skipped Pro read (printed; also returned for logs/tests)."""
    line = f"::notice title=Pro unavailable::{what} skipped - {why or reason() or REASON}"
    print(line, flush=True)
    return line


LEDGER_DIRS = ("output/prediction_ledger/pro", "output/prediction_ledger_settled/pro")
LEDGER_MAX_AGE_H = 36.0


def ledger_root(pro_root: Path | None) -> tuple[Path | None, str | None, dict | None]:
    """(root, reason, read_from) of Pro's prediction ledger for the predictions index / GW dataset.

    exec: the server copy (both ledger dirs PUBLISHED and as_of within 36 h), read_from = {"from": "server via exec",
    "produced_at", "as_of"}. github: --pro-root as before (None while PRO_REPO_AVAILABLE=0). none/unknown: None."""
    if source() == "exec":
        for d in LEDGER_DIRS:
            ok, why, info = exec_status(d, LEDGER_MAX_AGE_H)
            if not ok:
                notice("Pro prediction ledger", why)
                return None, why, None
        return exec_dir(), None, {"from": EXEC_LABEL, "produced_at": info.get("produced_at"),
                                  "as_of": info.get("as_of")}
    if not available():
        notice("Pro prediction ledger")
        return None, reason(), None
    pro = pro_root if pro_root and (Path(pro_root) / "output" / "prediction_ledger").exists() else None
    why = None if pro is not None else ("Pro ledger not readable this run" if pro_root else "no --pro-root given")
    if pro_root and pro is None:
        print(f"::warning::Pro ledger not found under {pro_root} - Pro marked UNAVAILABLE")
    return pro, why, ({"from": label()} if pro is not None else None)
