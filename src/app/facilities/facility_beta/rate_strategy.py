"""Facility Beta effective rate strategy."""

from decimal import Decimal

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityBetaRateStrategy:
    """Compute principal-weighted coupon with term factor for Facility Beta."""

    def compute(self, assets: list[NormalizedAsset]) -> Decimal:
        """Compute deterministic effective rate in percent units."""
        if not assets:
            return Decimal("0")

        numerator = Decimal("0")
        denominator = Decimal("0")
        for asset in sorted(assets, key=lambda item: item.asset_id):
            term_factor = Decimal(str(asset.term_days)) / Decimal("360")
            adjusted_coupon = asset.spread * term_factor
            numerator += asset.principal * adjusted_coupon
            denominator += asset.principal

        if denominator == 0:
            return Decimal("0")
        return numerator / denominator
