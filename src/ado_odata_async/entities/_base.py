"""Base Pydantic model for all entities: frozen + strict + extra-forbid (HR-4)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ODataEntity(BaseModel):
    """Strict, frozen base. All entity models inherit this."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
        populate_by_name=True,
    )
