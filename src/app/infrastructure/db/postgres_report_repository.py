"""PostgreSQL report repository implementation."""

import json

from app.domain.ports.report_repository import ReportRepository
from app.domain.value_objects.covenant_report import CovenantReport
from app.infrastructure.db.postgres import get_connection, to_json
from app.infrastructure.hash.canonical_hash import format_rate_two_decimals


class PostgresReportRepository(ReportRepository):
    """Persist and retrieve covenant reports from PostgreSQL."""

    def save_report(self, report: CovenantReport) -> int:
        """Persist full covenant report and return DB identifier."""
        sql = """
        INSERT INTO covenant_reports (
            facility_id,
            as_of_date,
            effective_rate,
            covenant_status,
            total_assets_evaluated,
            included_asset_ids,
            excluded_assets_with_reasons,
            report_hash
        )
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
        RETURNING id;
        """
        excluded = [
            {"asset_id": item.asset_id, "reason": item.reason}
            for item in report.excluded_assets_with_reasons
        ]

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        report.facility_id,
                        report.as_of_date,
                        format_rate_two_decimals(report.effective_rate),
                        report.covenant_status,
                        report.total_assets_evaluated,
                        to_json(report.included_asset_ids),
                        to_json(excluded),
                        report.report_hash,
                    ),
                )
                row = cursor.fetchone()
            connection.commit()

        if row is None:
            raise RuntimeError("Could not persist covenant report.")
        return int(row[0])

    def get_report(self, report_id: int) -> dict | None:
        """Fetch persisted report row by identifier."""
        sql = """
        SELECT
            id,
            facility_id,
            as_of_date,
            effective_rate,
            covenant_status,
            total_assets_evaluated,
            included_asset_ids,
            excluded_assets_with_reasons,
            report_hash,
            blockchain_status,
            blockchain_tx_hash,
            blockchain_error,
            created_at
        FROM covenant_reports
        WHERE id = %s;
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (report_id,))
                row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "facility_id": row[1],
            "as_of_date": row[2].isoformat(),
            "effective_rate": row[3],
            "covenant_status": row[4],
            "total_assets_evaluated": row[5],
            "included_asset_ids": row[6],
            "excluded_assets_with_reasons": row[7],
            "report_hash": row[8],
            "blockchain_status": row[9],
            "blockchain_tx_hash": row[10],
            "blockchain_error": row[11],
            "created_at": row[12].isoformat(),
        }

    def set_blockchain_result(
        self,
        report_id: int,
        status: str,
        tx_hash: str | None,
        error_message: str | None,
    ) -> None:
        """Update blockchain publication metadata for an existing report."""
        sql = """
        UPDATE covenant_reports
        SET blockchain_status = %s,
            blockchain_tx_hash = %s,
            blockchain_error = %s
        WHERE id = %s;
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (status, tx_hash, error_message, report_id))
            connection.commit()
