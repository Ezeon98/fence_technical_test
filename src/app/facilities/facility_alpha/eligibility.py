"""Facility Alpha eligibility strategy."""

from app.domain.value_objects.covenant_report import ExcludedAsset
from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityAlphaEligibility:
    """Apply Facility Alpha eligibility rules.

    Rules:
    - Asset must be active.
    - Principal must be positive.
    - Term must be <= 365 days.
    """

    def apply(
        self, assets: list[NormalizedAsset]
    ) -> tuple[list[NormalizedAsset], list[ExcludedAsset]]:
        """Return included and excluded assets with deterministic reasoning."""
        included: list[NormalizedAsset] = []
        excluded: list[ExcludedAsset] = []

        for asset in assets:
            if asset.status.lower() != "active":
                excluded.append(ExcludedAsset(asset_id=asset.asset_id, reason="inactive_status"))
                continue
            if asset.principal <= 0:
                excluded.append(ExcludedAsset(asset_id=asset.asset_id, reason="invalid_principal"))
                continue
            if asset.term_days > 365:
                excluded.append(ExcludedAsset(asset_id=asset.asset_id, reason="term_exceeds_limit"))
                continue
            included.append(asset)

        included.sort(key=lambda item: item.asset_id)
        excluded.sort(key=lambda item: (item.asset_id, item.reason))
        return included, excluded
