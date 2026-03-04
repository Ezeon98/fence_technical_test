"""Integration tests for end-to-end covenant computation and persistence."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from urllib.parse import ParseResult, urlparse, urlunparse

import psycopg
import pytest
from psycopg import sql

from app.application.use_cases.compute_and_publish_covenant import (
    ComputeAndPublishCovenantUseCase,
)
from app.domain.ports.publisher import PublicationResult
from app.domain.value_objects.covenant_report import CovenantReport, ExcludedAsset
from app.facilities.registry import get_facility_bundle
from app.infrastructure.db.postgres import get_connection, initialize_database
from app.infrastructure.db.postgres_report_repository import PostgresReportRepository
from app.infrastructure.hash.canonical_hash import compute_report_hash
from app.infrastructure.publishers.database_publisher import DatabasePublisher
from app.infrastructure.settings import get_settings


@dataclass(frozen=True)
class FlowExpectation:
    """Expected deterministic covenant outputs for a facility scenario."""

    facility_id: str
    portfolio: dict[str, Any]
    effective_rate: Decimal
    covenant_status: str
    included_asset_ids: list[str]
    excluded_assets_with_reasons: list[ExcludedAsset]


class DeterministicSmartContractPublisher:
    """Fake blockchain publisher with stable deterministic tx hashes."""

    def publish(self, report: CovenantReport) -> PublicationResult:
        """Return a deterministic tx reference derived from report hash."""
        tx_hash = f"0x{report.report_hash[:64]}"
        return PublicationResult(success=True, reference=tx_hash)


def _resolve_test_database_url() -> str:
    """Resolve a safe database URL for integration tests.

    Priority order:
    1. TEST_DATABASE_URL environment variable.
    2. Localhost fallback database suitable for dockerized PostgreSQL.
    """
    explicit_url = os.environ.get("TEST_DATABASE_URL")
    if explicit_url:
        return explicit_url

    return "postgresql://postgres:postgres@postgres:5432/covenants_test"


def _database_name_from_url(database_url: str) -> str:
    """Extract database name from a PostgreSQL connection URL."""
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip("/")
    if not db_name:
        raise ValueError("Database URL must include a database name.")
    return db_name


def _admin_database_url(database_url: str) -> str:
    """Build a connection URL that targets the postgres admin database."""
    parsed = urlparse(database_url)
    admin_parsed = ParseResult(
        scheme=parsed.scheme,
        netloc=parsed.netloc,
        path="/postgres",
        params=parsed.params,
        query=parsed.query,
        fragment=parsed.fragment,
    )
    return urlunparse(admin_parsed)


def _ensure_database_exists(database_url: str) -> None:
    """Create the target database if it does not already exist."""
    database_name = _database_name_from_url(database_url)
    admin_url = _admin_database_url(database_url)

    with psycopg.connect(admin_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s;",
                (database_name,),
            )
            exists = cursor.fetchone() is not None
            if not exists:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {};").format(sql.Identifier(database_name))
                )


@pytest.fixture(scope="session", autouse=True)
def configure_test_database_environment() -> None:
    """Configure the app to use a dedicated PostgreSQL test database."""
    database_url = _resolve_test_database_url()

    original_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()

    try:
        _ensure_database_exists(database_url)
        initialize_database()
    except Exception as error:  # pragma: no cover - environment dependent
        pytest.skip(f"PostgreSQL integration tests skipped: {error}")

    yield

    if original_database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = original_database_url
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clean_covenant_reports_table() -> None:
    """Ensure each test starts with a clean covenant_reports table."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE covenant_reports RESTART IDENTITY;")
        connection.commit()


@pytest.fixture()
def report_repository() -> PostgresReportRepository:
    """Return a real PostgreSQL report repository instance."""
    return PostgresReportRepository()


def _build_use_case(
    facility_id: str,
    report_repository: PostgresReportRepository,
) -> ComputeAndPublishCovenantUseCase:
    """Build use case with real DB publisher and deterministic chain stub."""
    bundle = get_facility_bundle(facility_id)
    database_publisher = DatabasePublisher(repository=report_repository)
    smart_contract_publisher = DeterministicSmartContractPublisher()

    return ComputeAndPublishCovenantUseCase(
        mapper=bundle.mapper,
        eligibility=bundle.eligibility,
        rate_strategy=bundle.rate_strategy,
        covenant_threshold=bundle.covenant_threshold,
        report_repository=report_repository,
        database_publisher=database_publisher,
        smart_contract_publisher=smart_contract_publisher,
    )


def _build_expected_hash(expectation: FlowExpectation, as_of_date: date) -> str:
    """Compute the expected deterministic hash from known output fields."""
    report = CovenantReport(
        facility_id=expectation.facility_id,
        as_of_date=as_of_date.isoformat(),
        effective_rate=expectation.effective_rate,
        covenant_status=expectation.covenant_status,
        total_assets_evaluated=len(expectation.portfolio["assets"]),
        included_asset_ids=expectation.included_asset_ids,
        excluded_assets_with_reasons=expectation.excluded_assets_with_reasons,
        report_hash="",
    )
    return compute_report_hash(report)


@pytest.fixture(
    params=[
        FlowExpectation(
            facility_id="facility_educa",
            portfolio={
                "assets": [
                    {
                        "external_id": "EDU-001",
                        "status": "open",
                        "is_eligible": True,
                        "outstanding_amount": "10000.00",
                        "interest_rate_percentage": "18.50",
                        "loan_status": "current",
                    },
                    {
                        "external_id": "EDU-002",
                        "status": "open",
                        "is_eligible": True,
                        "outstanding_amount": "8300.00",
                        "interest_rate_percentage": None,
                        "loan_status": "current",
                    },
                    {
                        "external_id": "EDU-003",
                        "status": "closed",
                        "is_eligible": True,
                        "outstanding_amount": "5000.00",
                        "interest_rate_percentage": "15.20",
                        "loan_status": "current",
                    },
                ]
            },
            effective_rate=Decimal("18.50"),
            covenant_status="COMPLIANT",
            included_asset_ids=["EDU-001"],
            excluded_assets_with_reasons=[
                ExcludedAsset(
                    asset_id="EDU-002",
                    reason="missing_interest_rate",
                ),
                ExcludedAsset(asset_id="EDU-003", reason="status_not_open"),
            ],
        ),
        FlowExpectation(
            facility_id="facility_payearly",
            portfolio={
                "assets": [
                    {
                        "external_id": "PAY-001",
                        "status": "performing",
                        "is_eligible": True,
                        "outstanding_principal_amount": "2000.00",
                        "total_principal_amount": "2500.00",
                        "total_fee_amount": "75.00",
                        "created_at": "2026-01-10T00:00:00Z",
                        "due_date": "2026-02-10",
                    },
                    {
                        "external_id": "PAY-002",
                        "status": "performing",
                        "is_eligible": False,
                        "outstanding_principal_amount": "1100.00",
                        "total_principal_amount": "1300.00",
                        "total_fee_amount": "39.00",
                        "created_at": "2026-01-05T00:00:00Z",
                        "due_date": "2026-01-20",
                    },
                    {
                        "external_id": "PAY-003",
                        "status": "performing",
                        "is_eligible": True,
                        "outstanding_principal_amount": "0.00",
                        "total_principal_amount": "900.00",
                        "total_fee_amount": "18.00",
                        "created_at": "2026-01-15T00:00:00Z",
                        "due_date": "2026-01-30",
                    },
                ]
            },
            effective_rate=Decimal("0.35"),
            covenant_status="COMPLIANT",
            included_asset_ids=["PAY-001"],
            excluded_assets_with_reasons=[
                ExcludedAsset(asset_id="PAY-002", reason="not_eligible"),
                ExcludedAsset(
                    asset_id="PAY-003",
                    reason="no_outstanding_principal",
                ),
            ],
        ),
        FlowExpectation(
            facility_id="facility_nomina",
            portfolio={
                "assets": [
                    {
                        "external_id": "NOM-001",
                        "status": "active",
                        "is_eligible": True,
                        "outstanding_amount": "4500.00",
                        "fee_percentage": "0.12",
                        "origination_date": "2026-01-01",
                        "maturity_date": "01/04/2026",
                    },
                    {
                        "external_id": "NOM-002",
                        "status": "active",
                        "is_eligible": False,
                        "outstanding_amount": "2200.00",
                        "fee_percentage": "0.10",
                        "origination_date": "2026-01-15",
                        "maturity_date": "15/03/2026",
                    },
                    {
                        "external_id": "NOM-003",
                        "status": "inactive",
                        "is_eligible": True,
                        "outstanding_amount": "3100.00",
                        "fee_percentage": "0.11",
                        "origination_date": "2026-02-01",
                        "maturity_date": "01/05/2026",
                    },
                ]
            },
            effective_rate=Decimal("0.48"),
            covenant_status="COMPLIANT",
            included_asset_ids=["NOM-001"],
            excluded_assets_with_reasons=[
                ExcludedAsset(asset_id="NOM-002", reason="not_eligible"),
                ExcludedAsset(
                    asset_id="NOM-003",
                    reason="status_not_active",
                ),
            ],
        ),
    ],
    ids=["facility_educa", "facility_payearly", "facility_nomina"],
)
def facility_expectation(request: pytest.FixtureRequest) -> FlowExpectation:
    """Provide per-facility integration scenario expectations."""
    return request.param


def test_full_covenant_flow_for_each_facility(
    report_repository: PostgresReportRepository,
    facility_expectation: FlowExpectation,
) -> None:
    """Validate full use-case flow and persisted report for each facility."""
    as_of_date = date(2026, 3, 4)
    use_case = _build_use_case(
        facility_id=facility_expectation.facility_id,
        report_repository=report_repository,
    )

    result = use_case.execute(
        facility_id=facility_expectation.facility_id,
        as_of_date=as_of_date,
        raw_portfolio=facility_expectation.portfolio,
    )

    report = result["report"]
    expected_hash = _build_expected_hash(facility_expectation, as_of_date)

    assert report.effective_rate == facility_expectation.effective_rate
    assert report.covenant_status == facility_expectation.covenant_status
    assert report.included_asset_ids == facility_expectation.included_asset_ids
    assert (
        report.excluded_assets_with_reasons
        == facility_expectation.excluded_assets_with_reasons
    )
    assert report.report_hash == expected_hash

    persisted = report_repository.get_report(result["report_id"])
    assert persisted is not None
    assert persisted["included_asset_ids"] == facility_expectation.included_asset_ids
    assert persisted["excluded_assets_with_reasons"] == [
        {"asset_id": item.asset_id, "reason": item.reason}
        for item in facility_expectation.excluded_assets_with_reasons
    ]
    assert persisted["report_hash"] == expected_hash


def test_idempotency_same_input_returns_same_report_id(
    report_repository: PostgresReportRepository,
) -> None:
    """Validate ON CONFLICT idempotency with real database persistence."""
    as_of_date = date(2026, 3, 4)
    facility_id = "facility_educa"
    portfolio = {
        "assets": [
            {
                "external_id": "EDU-001",
                "status": "open",
                "is_eligible": True,
                "outstanding_amount": "10000.00",
                "interest_rate_percentage": "18.50",
                "loan_status": "current",
            },
            {
                "external_id": "EDU-002",
                "status": "open",
                "is_eligible": True,
                "outstanding_amount": "8300.00",
                "interest_rate_percentage": None,
                "loan_status": "current",
            },
            {
                "external_id": "EDU-003",
                "status": "closed",
                "is_eligible": True,
                "outstanding_amount": "5000.00",
                "interest_rate_percentage": "15.20",
                "loan_status": "current",
            },
        ]
    }

    use_case = _build_use_case(
        facility_id=facility_id,
        report_repository=report_repository,
    )

    first_result = use_case.execute(
        facility_id=facility_id,
        as_of_date=as_of_date,
        raw_portfolio=portfolio,
    )
    second_result = use_case.execute(
        facility_id=facility_id,
        as_of_date=as_of_date,
        raw_portfolio=portfolio,
    )

    first_report_id = first_result["report_id"]
    second_report_id = second_result["report_id"]
    report_hash = first_result["report"].report_hash

    assert second_report_id == first_report_id
    assert second_result["report"].report_hash == report_hash

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM covenant_reports WHERE report_hash = %s;",
                (report_hash,),
            )
            count_for_hash = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM covenant_reports;")
            total_count = int(cursor.fetchone()[0])

    assert count_for_hash == 1
    assert total_count == 1
