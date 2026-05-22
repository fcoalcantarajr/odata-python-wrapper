"""Base Pydantic model for all entities: frozen + strict + extra-forbid (HR-4)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError


class ODataEntity(BaseModel):
    """Strict, frozen base. All entity models inherit this."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
        populate_by_name=True,
    )

    def __setattr__(self, name: str, value: Any) -> None:
        """Override to raise TypeError (Pydantic v1 compat) on frozen mutation.

        Pydantic v2 raises ``ValidationError`` for frozen instances, but
        AC-5 expects ``TypeError`` with ``"immutable"`` in the message.
        """
        try:
            super().__setattr__(name, value)
        except ValidationError as exc:
            msg = f"'{type(self).__name__}' object is immutable"
            raise TypeError(msg) from exc
