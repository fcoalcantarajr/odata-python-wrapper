"""PAT handling helpers (mask, validate format)."""

from __future__ import annotations

import aiohttp


def build_basic_auth(pat: str) -> aiohttp.BasicAuth:
    raise NotImplementedError("SPEC-002 will implement auth construction")


def mask_pat(pat: str) -> str:
    return pat[:6] + "..."
