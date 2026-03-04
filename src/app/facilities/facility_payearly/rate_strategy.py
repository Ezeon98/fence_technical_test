"""Facility PayEarly rate strategy."""

from decimal import Decimal

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityPayearlyRateStrategy:
    """Compute annualized fee yield weighted by outstanding principal."""

    def compute(self, assets: list[NormalizedAsset]) -> Decimal:
        """Compute effective rate using PayEarly annualized fee yield."""
        numerator = Decimal("0")
        denominator = Decimal("0")

        for asset in sorted(assets, key=lambda item: item.asset_id):
            if asset.created_at is None or asset.due_date is None:
                continue
            if asset.total_principal_amount is None:
                continue
            if asset.total_fee_amount is None:
                continue
            if asset.outstanding_principal_amount is None:
                continue
            if asset.total_principal_amount <= Decimal("0"):
                continue

            tenor_days = (asset.due_date - asset.created_at).days
            if tenor_days <= 0:
                continue

            fee_yield = (
                asset.total_fee_amount
                / asset.total_principal_amount
                * (Decimal("365") / Decimal(tenor_days))
            )
            numerator += asset.outstanding_principal_amount * fee_yield
            denominator += asset.outstanding_principal_amount

        if denominator == 0:
            return Decimal("0")
        return numerator / denominator
