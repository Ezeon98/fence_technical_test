"""Covenant API routes."""

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.use_cases.compute_and_publish_covenant import (
    ComputeAndPublishCovenantUseCase,
)
from app.facilities.registry import get_facility_bundle
from app.infrastructure.db.postgres_report_repository import (
    PostgresReportRepository,
)
from app.infrastructure.hash.canonical_hash import format_rate_two_decimals
from app.infrastructure.publishers.database_publisher import DatabasePublisher
from app.infrastructure.publishers.smart_contract_publisher import (
    SmartContractPublisher,
)


router = APIRouter(prefix="/covenants", tags=["covenants"])


class ComputeCovenantRequest(BaseModel):
    """Request schema for covenant computation endpoint."""

    facility_id: str = Field(min_length=1)
    as_of_date: date
    portfolio_json: dict[str, Any]


class ExcludedAssetSchema(BaseModel):
    """Excluded asset schema."""

    asset_id: str
    reason: str


class CovenantReportSchema(BaseModel):
    """Covenant report response schema."""

    facility_id: str
    as_of_date: str
    effective_rate: str
    covenant_status: str
    total_assets_evaluated: int
    included_asset_ids: list[str]
    excluded_assets_with_reasons: list[ExcludedAssetSchema]
    report_hash: str


class ComputeCovenantResponse(BaseModel):
    """Response schema for covenant computation endpoint."""

    report_id: int
    report: CovenantReportSchema
    database_publication: dict[str, Any]
    blockchain_publication: dict[str, Any]


@router.post("/compute", response_model=ComputeCovenantResponse)
def compute_covenant(payload: ComputeCovenantRequest) -> ComputeCovenantResponse:
    """Compute, persist, and publish covenant for a facility payload."""
    try:
        facility_bundle = get_facility_bundle(payload.facility_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

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
    result = use_case.execute(
        facility_id=payload.facility_id,
        as_of_date=payload.as_of_date,
        raw_portfolio=payload.portfolio_json,
    )

    report = result["report"]
    response_report = CovenantReportSchema(
        facility_id=report.facility_id,
        as_of_date=report.as_of_date,
        effective_rate=format_rate_two_decimals(report.effective_rate),
        covenant_status=report.covenant_status,
        total_assets_evaluated=report.total_assets_evaluated,
        included_asset_ids=sorted(report.included_asset_ids),
        excluded_assets_with_reasons=[
            ExcludedAssetSchema(asset_id=item.asset_id, reason=item.reason)
            for item in report.excluded_assets_with_reasons
        ],
        report_hash=report.report_hash,
    )

    return ComputeCovenantResponse(
        report_id=result["report_id"],
        report=response_report,
        database_publication=result["database_publication"],
        blockchain_publication=result["blockchain_publication"],
    )


@router.get("/{report_id}")
def get_covenant_report(report_id: int) -> dict[str, Any]:
    """Fetch a previously persisted covenant report."""
    repository = PostgresReportRepository()
    result = repository.get_report(report_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return result
