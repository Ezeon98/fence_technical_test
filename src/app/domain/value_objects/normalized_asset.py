"""Normalized asset value object."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class NormalizedAsset:
    """Canonical asset representation used by the domain layer.

    This object is the strict boundary between facility raw JSON payloads and
    the deterministic covenant computation logic.
    """

    asset_id: str
    principal: Decimal
    spread: Decimal
    term_days: int
    status: str
