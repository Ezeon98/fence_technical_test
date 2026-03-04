"""Facility Alpha raw JSON to normalized assets mapper."""

from decimal import Decimal
from typing import Any

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityAlphaMapper:
    """Map Facility Alpha payloads to normalized assets.

    Expected raw schema example:
    {
        "assets": [
            {
                "id": "A-1",
                "principal": "10000.00",
                "spread_pct": "4.20",
                "days": 180,
                "state": "active"
            }
        ]
    }
    """

    def map_assets(self, raw_payload: dict[str, Any]) -> list[NormalizedAsset]:
        """Convert Facility Alpha payload into canonical normalized assets."""
        assets_data = raw_payload.get("assets", [])
        normalized: list[NormalizedAsset] = []
        for item in assets_data:
            normalized.append(
                NormalizedAsset(
                    asset_id=str(item["id"]),
                    status=str(item.get("state", "")).lower(),
                    is_eligible=bool(item.get("is_eligible", True)),
                    outstanding_amount=Decimal(str(item.get("principal", "0"))),
                    interest_rate_percentage=Decimal(
                        str(item.get("spread_pct", "0"))
                    ),
                )
            )
        return normalized
