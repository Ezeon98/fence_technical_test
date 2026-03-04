"""Facility Nomina mapper."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.domain.value_objects.normalized_asset import NormalizedAsset


class FacilityNominaMapper:
    """Map Nomina facility raw payload into normalized assets."""

    def map_assets(self, raw_payload: dict[str, Any]) -> list[NormalizedAsset]:
        """Convert raw Nomina JSON objects into NormalizedAsset entries."""
        assets_data = self._extract_assets(raw_payload)
        normalized: list[NormalizedAsset] = []
        for item in assets_data:
            normalized.append(
                NormalizedAsset(
                    asset_id=str(item["external_id"]),
                    status=str(item.get("status", "")).lower(),
                    is_eligible=bool(item.get("is_eligible", False)),
                    outstanding_amount=Decimal(
                        str(item.get("outstanding_amount", "0"))
                    ),
                    fee_percentage=Decimal(str(item.get("fee_percentage", "0"))),
                    origination_date=self._parse_ymd(item.get("origination_date")),
                    maturity_date=self._parse_dmy(item.get("maturity_date")),
                )
            )
        return normalized

    def _extract_assets(self, raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract Nomina asset records from supported container shapes."""
        if isinstance(raw_payload.get("assets"), list):
            return raw_payload["assets"]
        if isinstance(raw_payload.get("portfolio"), list):
            return raw_payload["portfolio"]
        return []

    def _parse_ymd(self, value: Any) -> date | None:
        """Parse a date value in YYYY-MM-DD format."""
        if value is None:
            return None
        return datetime.strptime(str(value), "%Y-%m-%d").date()

    def _parse_dmy(self, value: Any) -> date | None:
        """Parse a date value in DD/MM/YYYY format."""
        if value is None:
            return None
        return datetime.strptime(str(value), "%d/%m/%Y").date()
