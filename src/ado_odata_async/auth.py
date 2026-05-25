"""PAT handling helpers (mask, validate format)."""

from __future__ import annotations

import aiohttp


def build_basic_auth(pat: str) -> aiohttp.BasicAuth:
    return aiohttp.BasicAuth("", pat)


def mask_pat(pat: str) -> str:
    return pat[:6] + "..."
