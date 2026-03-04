"""Facility Beta raw JSON to normalized assets mapper."""

from decimal import Decimal
from typing import Any

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityBetaMapper:
    """Map Facility Beta payloads to normalized assets.

    Expected raw schema example:
    {
        "portfolio": {
            "records": [
                {
                    "assetId": "B-1",
                    "notional": "25000.00",
                    "coupon": "6.10",
                    "maturityDays": 90,
                    "lifecycle": "performing"
                }
            ]
        }
    }
    """

    def map_assets(self, raw_payload: dict[str, Any]) -> list[NormalizedAsset]:
        """Convert Facility Beta payload into canonical normalized assets."""
        records = raw_payload.get("portfolio", {}).get("records", [])
        normalized: list[NormalizedAsset] = []
        for item in records:
            normalized.append(
                NormalizedAsset(
                    asset_id=str(item["assetId"]),
                    status=str(item.get("lifecycle", "")).lower(),
                    is_eligible=bool(item.get("is_eligible", True)),
                    outstanding_amount=Decimal(str(item.get("notional", "0"))),
                    interest_rate_percentage=Decimal(str(item.get("coupon", "0"))),
                )
            )
        return normalized
