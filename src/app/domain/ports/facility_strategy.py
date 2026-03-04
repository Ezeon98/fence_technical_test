"""Facility strategy ports."""

from decimal import Decimal
from typing import Any, Protocol

from app.domain.value_objects.covenant_report import ExcludedAsset
from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityMapper(Protocol):
    """Maps a facility raw JSON payload into normalized assets."""

    def map_assets(self, raw_payload: dict[str, Any]) -> list[NormalizedAsset]:
        """Convert raw facility payload into normalized assets."""


class EligibilityStrategy(Protocol):
    """Applies facility-specific eligibility criteria."""

    def apply(
        self, assets: list[NormalizedAsset]
    ) -> tuple[list[NormalizedAsset], list[ExcludedAsset]]:
        """Split assets into included and excluded groups."""


class EffectiveRateStrategy(Protocol):
    """Computes a facility-specific effective rate in percentage points."""

    def compute(self, assets: list[NormalizedAsset]) -> Decimal:
        """Compute deterministic rate and return Decimal percentage."""
