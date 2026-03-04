"""Facility Educa eligibility strategy."""

from app.domain.value_objects.covenant_report import ExcludedAsset
from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityEducaEligibility:
    """Apply Educa covenant eligibility rules."""

    def apply(
        self, assets: list[NormalizedAsset]
    ) -> tuple[list[NormalizedAsset], list[ExcludedAsset]]:
        """Split assets into included and excluded groups with reasons."""
        included: list[NormalizedAsset] = []
        excluded: list[ExcludedAsset] = []

        for asset in assets:
            if asset.status != "open":
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="status_not_open")
                )
                continue
            if not asset.is_eligible:
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="not_eligible")
                )
                continue
            if asset.loan_status != "current":
                excluded.append(
                    ExcludedAsset(
                        asset_id=asset.asset_id,
                        reason="loan_status_not_current",
                    )
                )
                continue
            if asset.interest_rate_percentage is None:
                excluded.append(
                    ExcludedAsset(
                        asset_id=asset.asset_id,
                        reason="missing_interest_rate",
                    )
                )
                continue
            included.append(asset)

        included.sort(key=lambda item: item.asset_id)
        excluded.sort(key=lambda item: (item.asset_id, item.reason))
        return included, excluded
