"""Facility Alpha eligibility strategy."""

from app.domain.value_objects.covenant_report import ExcludedAsset
from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityAlphaEligibility:
    """Apply Facility Alpha eligibility rules.

    Rules:
    - Asset must be active.
    - Outstanding amount must be positive.
    """

    def apply(
        self, assets: list[NormalizedAsset]
    ) -> tuple[list[NormalizedAsset], list[ExcludedAsset]]:
        """Return included and excluded assets with deterministic reasoning."""
        included: list[NormalizedAsset] = []
        excluded: list[ExcludedAsset] = []

        for asset in assets:
            if asset.status.lower() != "active":
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="inactive_status")
                )
                continue
            if (
                asset.outstanding_amount is None
                or asset.outstanding_amount <= 0
            ):
                excluded.append(
                    ExcludedAsset(asset_id=asset.asset_id, reason="invalid_principal")
                )
                continue
            included.append(asset)

        included.sort(key=lambda item: item.asset_id)
        excluded.sort(key=lambda item: (item.asset_id, item.reason))
        return included, excluded
