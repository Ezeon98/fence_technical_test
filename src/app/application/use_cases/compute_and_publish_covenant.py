"""Use case for covenant computation and publication."""

from dataclasses import replace
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.domain.ports.facility_strategy import (
    EffectiveRateStrategy,
    EligibilityStrategy,
    FacilityMapper,
)
from app.domain.ports.publisher import Publisher
from app.domain.ports.report_repository import ReportRepository
from app.domain.value_objects.covenant_report import CovenantReport
from app.infrastructure.hash.canonical_hash import compute_report_hash

TWO_DECIMAL = Decimal("0.01")


class ComputeAndPublishCovenantUseCase:
    """Orchestrates deterministic covenant calculation and publication."""

    def __init__(
        self,
        mapper: FacilityMapper,
        eligibility: EligibilityStrategy,
        rate_strategy: EffectiveRateStrategy,
        covenant_threshold: Decimal,
        report_repository: ReportRepository,
        database_publisher: Publisher,
        smart_contract_publisher: Publisher,
    ) -> None:
        """Initialize the use case with facility and infra dependencies."""
        self._mapper = mapper
        self._eligibility = eligibility
        self._rate_strategy = rate_strategy
        self._covenant_threshold = covenant_threshold
        self._report_repository = report_repository
        self._database_publisher = database_publisher
        self._smart_contract_publisher = smart_contract_publisher

    def execute(
        self,
        facility_id: str,
        as_of_date: date,
        raw_portfolio: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute covenant report, persist, and attempt blockchain publish."""
        assets = self._mapper.map_assets(raw_portfolio)
        included_assets, excluded_assets = self._eligibility.apply(assets)

        computed_rate = self._rate_strategy.compute(included_assets)
        rounded_rate = computed_rate.quantize(TWO_DECIMAL, rounding=ROUND_HALF_UP)
        status = self._evaluate_covenant(rounded_rate)

        report = CovenantReport(
            facility_id=facility_id,
            as_of_date=as_of_date.isoformat(),
            effective_rate=rounded_rate,
            covenant_status=status,
            total_assets_evaluated=len(assets),
            included_asset_ids=[asset.asset_id for asset in included_assets],
            excluded_assets_with_reasons=excluded_assets,
            report_hash="",
        )
        report_hash = compute_report_hash(report)
        hashed_report = replace(report, report_hash=report_hash)

        db_result = self._database_publisher.publish(hashed_report)
        if not db_result.success or db_result.reference is None:
            raise RuntimeError("Database publication failed.")

        report_id = int(db_result.reference)
        onchain = self._publish_to_chain(hashed_report, report_id)

        return {
            "report_id": report_id,
            "report": hashed_report,
            "database_publication": {
                "success": db_result.success,
                "reference": db_result.reference,
            },
            "blockchain_publication": onchain,
        }

    def _evaluate_covenant(self, effective_rate: Decimal) -> str:
        """Evaluate covenant status against facility threshold."""
        if effective_rate >= self._covenant_threshold:
            return "COMPLIANT"
        return "BREACH"

    def _publish_to_chain(
        self, report: CovenantReport, report_id: int
    ) -> dict[str, Any]:
        """Attempt blockchain publication with graceful error handling."""
        chain_result = self._smart_contract_publisher.publish(report)
        if chain_result.success:
            self._report_repository.set_blockchain_result(
                report_id=report_id,
                status="PUBLISHED",
                tx_hash=chain_result.reference,
                error_message=None,
            )
            return {
                "success": True,
                "tx_hash": chain_result.reference,
                "error": None,
            }

        self._report_repository.set_blockchain_result(
            report_id=report_id,
            status="FAILED",
            tx_hash=None,
            error_message=chain_result.error_message,
        )
        return {
            "success": False,
            "tx_hash": None,
            "error": chain_result.error_message,
        }
