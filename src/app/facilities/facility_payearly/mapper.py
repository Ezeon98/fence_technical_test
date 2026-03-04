"""Facility PayEarly mapper."""

from datetime import date
from decimal import Decimal
from typing import Any

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityPayearlyMapper:
    """Map PayEarly facility raw payload into normalized assets."""

    def map_assets(self, raw_payload: dict[str, Any]) -> list[NormalizedAsset]:
        """Convert raw PayEarly JSON objects into NormalizedAsset entries."""
        assets_data = self._extract_assets(raw_payload)
        normalized: list[NormalizedAsset] = []
        for item in assets_data:
            normalized.append(
                NormalizedAsset(
                    asset_id=str(item["external_id"]),
                    status=str(item.get("status", "")).lower(),
                    is_eligible=bool(item.get("is_eligible", False)),
                    outstanding_principal_amount=Decimal(
                        str(item.get("outstanding_principal_amount", "0"))
                    ),
                    total_principal_amount=Decimal(
                        str(item.get("total_principal_amount", "0"))
                    ),
                    total_fee_amount=Decimal(
                        str(item.get("total_fee_amount", "0"))
                    ),
                    created_at=self._parse_iso_date(item.get("created_at")),
                    due_date=self._parse_iso_date(item.get("due_date")),
                )
            )
        return normalized

    def _extract_assets(self, raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract PayEarly asset records from supported container shapes."""
        if isinstance(raw_payload.get("assets"), list):
            return raw_payload["assets"]
        if isinstance(raw_payload.get("portfolio"), list):
            return raw_payload["portfolio"]
        return []

    def _parse_iso_date(self, value: Any) -> date | None:
        """Parse ISO date or datetime text into a date object."""
        if value is None:
            return None
        text_value = str(value)
        date_part = text_value.split("T", maxsplit=1)[0]
        return date.fromisoformat(date_part)
