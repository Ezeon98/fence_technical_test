"""Facility Nomina eligibility strategy."""

from decimal import Decimal

from app.domain.value_objects.covenant_report import ExcludedAsset
from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityNominaEligibility:
    """Apply Nomina covenant eligibility rules."""

    def apply(
        self, assets: list[NormalizedAsset]
    ) -> tuple[list[NormalizedAsset], list[ExcludedAsset]]:
        """Split assets into included and excluded groups with reasons."""
        included: list[NormalizedAsset] = []
        excluded: list[ExcludedAsset] = []

        for asset in assets:
            if asset.status != "active":
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="status_not_active")
                )
                continue
            if not asset.is_eligible:
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="not_eligible")
                )
                continue
            outstanding = asset.outstanding_amount
            if outstanding is None or outstanding <= Decimal("0"):
                excluded.append(
                    ExcludedAsset(
                        asset_id=asset.asset_id,
                        reason="no_outstanding_amount",
                    )
                )
                continue
            included.append(asset)

        included.sort(key=lambda item: item.asset_id)
        excluded.sort(key=lambda item: (item.asset_id, item.reason))
        return included, excluded
