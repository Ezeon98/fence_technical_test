"""Facility Nomina rate strategy."""

from decimal import Decimal

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityNominaRateStrategy:
    """Compute annualized fee weighted by outstanding amount."""

    def compute(self, assets: list[NormalizedAsset]) -> Decimal:
        """Compute effective rate using repayment-month annualization."""
        numerator = Decimal("0")
        denominator = Decimal("0")

        for asset in sorted(assets, key=lambda item: item.asset_id):
            if asset.origination_date is None or asset.maturity_date is None:
                continue
            if asset.fee_percentage is None or asset.outstanding_amount is None:
                continue

            repayment_months = (
                (asset.maturity_date.year - asset.origination_date.year) * 12
                + asset.maturity_date.month
                - asset.origination_date.month
            )
            if repayment_months <= 0:
                continue

            annualized_fee = asset.fee_percentage * (
                Decimal("12") / Decimal(repayment_months)
            )
            numerator += asset.outstanding_amount * annualized_fee
            denominator += asset.outstanding_amount

        if denominator == 0:
            return Decimal("0")
        return numerator / denominator
