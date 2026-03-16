"""Reusable service for covenant computation and publication."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.application.use_cases.compute_and_publish_covenant import (
    ComputeAndPublishCovenantUseCase,
)
from app.facilities.registry import get_facility_bundle
from app.infrastructure.db.postgres_report_repository import (
    PostgresReportRepository,
)
from app.infrastructure.publishers.database_publisher import DatabasePublisher
from app.infrastructure.publishers.smart_contract_publisher import (
    SmartContractPublisher,
)


class CovenantProcessingService:
    """Run the covenant flow using existing use-case and infrastructure wiring."""

    def process(
        self,
        facility_id: str,
        as_of_date: date,
        portfolio_json: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute and publish a covenant report for a single payload."""
        facility_bundle = get_facility_bundle(facility_id)

        repository = PostgresReportRepository()
        database_publisher = DatabasePublisher(repository=repository)
        smart_publisher = SmartContractPublisher()

        use_case = ComputeAndPublishCovenantUseCase(
            mapper=facility_bundle.mapper,
            eligibility=facility_bundle.eligibility,
            rate_strategy=facility_bundle.rate_strategy,
            covenant_threshold=facility_bundle.covenant_threshold,
            report_repository=repository,
            database_publisher=database_publisher,
            smart_contract_publisher=smart_publisher,
        )
        return use_case.execute(
            facility_id=facility_id,
            as_of_date=as_of_date,
            raw_portfolio=portfolio_json,
        )
