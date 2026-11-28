"""One switch for every read of NevixAA/wowzaV9-Pro (owner 2026-11-28).

GitHub blocked the Pro repository on 2026-11-27 (every API and git access: 403 "Repository access
blocked"). The block may be lifted on appeal, so Pro is NOT removed from any config: it is marked
UNAVAILABLE by the repository variable PRO_REPO_AVAILABLE, which the workflows pass in as an env var.

    PRO_REPO_AVAILABLE unset / empty / anything else -> available (today's behaviour before the block)
    PRO_REPO_AVAILABLE = 0 | false | no | off         -> unavailable: every Pro source is skipped with a
                                                         notice, and each output that uses Pro data shows
                                                         it as UNAVAILABLE - never stale data as current,
                                                         never invented data, never a silent pass.

scripts/price_store_sync.py runs from a sparse checkout without src/ and carries the same rule inline.
"""
from __future__ import annotations

import os

ENV = "PRO_REPO_AVAILABLE"
REPO = "NevixAA/wowzaV9-Pro"
OFF = {"0", "false", "no", "off"}
REASON = f"source blocked: {REPO} is unavailable ({ENV}=0)"


def available(value: str | None = None) -> bool:
    """False only when the switch is explicitly off; unset means available."""
    v = os.getenv(ENV) if value is None else value
    return (v or "").strip().lower() not in OFF


def notice(what: str) -> str:
    """One GitHub Actions notice line for a skipped Pro read (printed; also returned for logs/tests)."""
    line = f"::notice title=Pro unavailable::{what} skipped - {REASON}"
    print(line, flush=True)
    return line
