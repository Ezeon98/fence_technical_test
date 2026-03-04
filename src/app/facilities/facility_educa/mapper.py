"""Facility Educa mapper."""

from decimal import Decimal
from typing import Any

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityEducaMapper:
    """Map Educa facility raw payload into normalized assets."""

    def map_assets(self, raw_payload: dict[str, Any]) -> list[NormalizedAsset]:
        """Convert raw Educa JSON objects into NormalizedAsset entries."""
        assets_data = self._extract_assets(raw_payload)
        normalized: list[NormalizedAsset] = []
        for item in assets_data:
            interest_rate = item.get("interest_rate_percentage")
            normalized.append(
                NormalizedAsset(
                    asset_id=str(item["external_id"]),
                    status=str(item.get("status", "")).lower(),
                    is_eligible=bool(item.get("is_eligible", False)),
                    outstanding_amount=Decimal(
                        str(item.get("outstanding_amount", "0"))
                    ),
                    interest_rate_percentage=(
                        Decimal(str(interest_rate))
                        if interest_rate is not None
                        else None
                    ),
                    loan_status=item.get("loan_status"),
                )
            )
        return normalized

    def _extract_assets(self, raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract Educa asset records from supported container shapes."""
        if isinstance(raw_payload.get("assets"), list):
            return raw_payload["assets"]
        if isinstance(raw_payload.get("portfolio"), list):
            return raw_payload["portfolio"]
        return []
