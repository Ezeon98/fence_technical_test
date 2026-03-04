"""Unit tests for deterministic covenant hashing."""

from decimal import Decimal

from app.domain.value_objects.covenant_report import CovenantReport, ExcludedAsset
from app.infrastructure.hash.canonical_hash import (
    canonical_report_payload,
    compute_report_hash,
)


def build_report() -> CovenantReport:
    """Build a report fixture with intentionally unsorted lists."""
    return CovenantReport(
        facility_id="facility_alpha",
        as_of_date="2026-03-04",
        effective_rate=Decimal("18.54"),
        covenant_status="COMPLIANT",
        total_assets_evaluated=3,
        included_asset_ids=["asset-3", "asset-1", "asset-2"],
        excluded_assets_with_reasons=[
            ExcludedAsset(asset_id="asset-8", reason="inactive_status"),
            ExcludedAsset(asset_id="asset-7", reason="invalid_principal"),
        ],
        report_hash="",
    )


def test_hash_is_reproducible_for_same_input() -> None:
    """Verify same deterministic data yields identical SHA-256 hash."""
    report_one = build_report()
    report_two = build_report()

    hash_one = compute_report_hash(report_one)
    hash_two = compute_report_hash(report_two)

    assert hash_one == hash_two


def test_payload_excludes_non_deterministic_fields() -> None:
    """Verify payload boundary contains only deterministic covenant fields."""
    payload = canonical_report_payload(build_report())

    assert set(payload.keys()) == {
        "facility_id",
        "as_of_date",
        "effective_rate",
        "covenant_status",
        "included_asset_ids",
        "excluded_assets_with_reasons",
    }
