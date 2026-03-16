"""Covenant API routes."""

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.services.covenant_processing_service import (
    CovenantProcessingService,
)
from app.application.services.sqs_message_processor import (
    SqsMessageProcessor,
    SqsProcessingSummary,
)
from app.infrastructure.hash.canonical_hash import format_rate_two_decimals
from app.infrastructure.settings import get_settings
from app.infrastructure.sqs.sqs_client import SqsClient

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


class ProcessSqsMessagesResponse(BaseModel):
    """Response schema for SQS batch processing endpoint."""

    polled_messages: int
    processed_successfully: int
    sent_to_dlq: int
    errors: list[str]


def _build_compute_covenant_response(
    result: dict[str, Any],
) -> ComputeCovenantResponse:
    """Map use-case output into API response schema."""
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


def _build_sqs_client() -> SqsClient:
    """Construct SQS client from environment-backed settings."""
    settings = get_settings()
    return SqsClient(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


@router.post("/compute", response_model=ComputeCovenantResponse)
def compute_covenant(payload: ComputeCovenantRequest) -> ComputeCovenantResponse:
    """Compute, persist, and publish covenant for a facility payload."""
    try:
        service = CovenantProcessingService()
        result = service.process(
            facility_id=payload.facility_id,
            as_of_date=payload.as_of_date,
            portfolio_json=payload.portfolio_json,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return _build_compute_covenant_response(result)


@router.post(
    "/process-sqs-messages",
    response_model=ProcessSqsMessagesResponse,
)
def process_sqs_messages() -> ProcessSqsMessagesResponse:
    """Poll source SQS queue and process covenant messages in batch."""
    settings = get_settings()
    if not settings.sqs_queue_url:
        raise HTTPException(status_code=500, detail="Missing SQS_QUEUE_URL.")
    if not settings.sqs_dlq_url:
        raise HTTPException(status_code=500, detail="Missing SQS_DLQ_URL.")
    if not settings.aws_access_key_id:
        raise HTTPException(status_code=500, detail="Missing AWS_ACCESS_KEY_ID.")
    if not settings.aws_secret_access_key:
        raise HTTPException(status_code=500, detail="Missing AWS_SECRET_ACCESS_KEY.")

    processor = SqsMessageProcessor(
        sqs_client=_build_sqs_client(),
        covenant_processing_service=CovenantProcessingService(),
        queue_url=settings.sqs_queue_url,
        dlq_url=settings.sqs_dlq_url,
    )
    summary: SqsProcessingSummary = processor.process_messages()

    return ProcessSqsMessagesResponse(
        polled_messages=summary.polled_messages,
        processed_successfully=summary.processed_successfully,
        sent_to_dlq=summary.sent_to_dlq,
        errors=summary.errors,
    )


@router.get("/{report_id}")
def get_covenant_report(report_id: int) -> dict[str, Any]:
    """Fetch a previously persisted covenant report."""
    repository = PostgresReportRepository()
    result = repository.get_report(report_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return result
