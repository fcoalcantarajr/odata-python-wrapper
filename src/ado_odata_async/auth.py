"""PAT handling helpers (mask, validate format). Stubs."""

from __future__ import annotations

import aiohttp


def build_basic_auth(pat: str) -> aiohttp.BasicAuth:
    """Return BasicAuth with EMPTY username (HR-8). The only correct shape for ADO Analytics."""
    raise NotImplementedError("SPEC-002 will implement auth construction")


def mask_pat(pat: str) -> str:
    """Mask all but the last 6 chars of a PAT (HR-16). Use everywhere PAT could be logged."""
    raise NotImplementedError("SPEC-002 will implement PAT masking")
