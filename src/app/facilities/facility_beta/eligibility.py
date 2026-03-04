"""Facility Beta eligibility strategy."""

from app.domain.value_objects.covenant_report import ExcludedAsset
from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityBetaEligibility:
    """Apply Facility Beta eligibility rules.

    Rules:
    - Asset must be performing.
    - Principal must be >= 1000.
    - Term must be <= 540 days.
    """

    def apply(
        self, assets: list[NormalizedAsset]
    ) -> tuple[list[NormalizedAsset], list[ExcludedAsset]]:
        """Return included and excluded assets with deterministic reasoning."""
        included: list[NormalizedAsset] = []
        excluded: list[ExcludedAsset] = []

        for asset in assets:
            if asset.status.lower() != "performing":
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="non_performing")
                )
                continue
            if asset.principal < 1000:
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="below_minimum")
                )
                continue
            if asset.term_days > 540:
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="term_exceeds_limit")
                )
                continue
            included.append(asset)

        included.sort(key=lambda item: item.asset_id)
        excluded.sort(key=lambda item: (item.asset_id, item.reason))
        return included, excluded
