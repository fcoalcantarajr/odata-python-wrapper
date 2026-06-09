"""PAT handling helpers (mask, validate format)."""

from __future__ import annotations

import aiohttp


def build_basic_auth(pat: str) -> aiohttp.BasicAuth:
    """Create aiohttp BasicAuth with empty username for Azure DevOps PAT auth.

    Azure DevOps requires an empty username when using PAT authentication.
    Any non-empty username value results in HTTP 401 (HR-8 gotcha 1).

    Args:
        pat: Personal Access Token string.

    Returns:
        aiohttp.BasicAuth configured with empty username and PAT as password.
    """
    return aiohttp.BasicAuth("", pat)


def mask_pat(pat: str) -> str:
    """Mask a PAT for safe logging.

    Returns only the first 6 characters followed by ellipsis to prevent
    accidental credential exposure in logs (HR-16).

    Args:
        pat: Personal Access Token string.

    Returns:
        Masked string like "abc123...".
    """
    return pat[:6] + "..."
