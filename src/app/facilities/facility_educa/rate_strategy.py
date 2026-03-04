"""Facility Educa rate strategy."""

from decimal import Decimal

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityEducaRateStrategy:
    """Compute weighted average interest rate for Educa assets."""

    def compute(self, assets: list[NormalizedAsset]) -> Decimal:
        """Compute effective rate using outstanding-weighted average."""
        if not assets:
            return Decimal("0")

        numerator = Decimal("0")
        denominator = Decimal("0")

        for asset in sorted(assets, key=lambda item: item.asset_id):
            if asset.outstanding_amount is None:
                continue
            if asset.interest_rate_percentage is None:
                continue
            numerator += asset.outstanding_amount * asset.interest_rate_percentage
            denominator += asset.outstanding_amount

        if denominator == 0:
            return Decimal("0")
        return numerator / denominator
