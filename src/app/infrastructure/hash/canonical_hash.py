"""Deterministic canonical payload and SHA-256 hash utilities."""

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP

from app.domain.value_objects.covenant_report import CovenantReport

TWO_DECIMAL = Decimal("0.01")


def format_rate_two_decimals(rate: Decimal) -> str:
    """Format a rate as a deterministic two-decimal string."""
    rounded = rate.quantize(TWO_DECIMAL, rounding=ROUND_HALF_UP)
    return format(rounded, "f")


def _sorted_excluded(report: CovenantReport) -> list[dict[str, str]]:
    """Return excluded assets sorted deterministically by id then reason."""
    sorted_items = sorted(
        report.excluded_assets_with_reasons,
        key=lambda item: (item.asset_id, item.reason),
    )
    return [{"asset_id": item.asset_id, "reason": item.reason} for item in sorted_items]


def canonical_report_payload(report: CovenantReport) -> dict:
    """Build canonical deterministic payload for covenant hashing.

    The payload intentionally excludes persistence metadata such as database
    identifiers, transaction hashes, and timestamps.
    """
    return {
        "facility_id": report.facility_id,
        "as_of_date": report.as_of_date,
        "effective_rate": format_rate_two_decimals(report.effective_rate),
        "covenant_status": report.covenant_status,
        "included_asset_ids": sorted(report.included_asset_ids),
        "excluded_assets_with_reasons": _sorted_excluded(report),
    }


def serialize_canonical_payload(payload: dict) -> str:
    """Serialize canonical payload into deterministic JSON text."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_report_hash(report: CovenantReport) -> str:
    """Compute a reproducible SHA-256 hash from canonical covenant payload."""
    payload = canonical_report_payload(report)
    serialized = serialize_canonical_payload(payload)
    digest = hashlib.sha256(serialized.encode("utf-8"))
    return digest.hexdigest()


def effective_rate_to_bps(rate: Decimal) -> int:
    """Convert percent rate into integer basis points without floats.

    Example: 18.54% -> 1854 bps.
    """
    rounded = rate.quantize(TWO_DECIMAL, rounding=ROUND_HALF_UP)
    return int((rounded * Decimal("100")).quantize(Decimal("1")))
