"""Facility Alpha effective rate strategy."""

from decimal import Decimal

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityAlphaRateStrategy:
    """Compute weighted average spread by principal for Facility Alpha."""

    def compute(self, assets: list[NormalizedAsset]) -> Decimal:
        """Compute deterministic weighted effective rate in percent units."""
        if not assets:
            return Decimal("0")

        numerator = Decimal("0")
        denominator = Decimal("0")
        for asset in sorted(assets, key=lambda item: item.asset_id):
            numerator += asset.principal * asset.spread
            denominator += asset.principal

        if denominator == 0:
            return Decimal("0")
        return numerator / denominator
