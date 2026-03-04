"""Repository port for covenant reports."""

from typing import Protocol

from app.domain.value_objects.covenant_report import CovenantReport


class ReportRepository(Protocol):
    """Persistence interface for covenant reports."""

    def save_report(self, report: CovenantReport) -> int:
        """Persist a report and return its database identifier."""

    def get_report(self, report_id: int) -> dict | None:
        """Fetch a persisted report by identifier."""

    def set_blockchain_result(
        self,
        report_id: int,
        status: str,
        tx_hash: str | None,
        error_message: str | None,
    ) -> None:
        """Persist blockchain publication metadata for a report."""
