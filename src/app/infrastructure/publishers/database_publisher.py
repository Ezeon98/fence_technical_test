"""Database publisher implementation."""

from app.domain.ports.publisher import PublicationResult, Publisher
from app.domain.ports.report_repository import ReportRepository
from app.domain.value_objects.covenant_report import CovenantReport


class DatabasePublisher(Publisher):
    """Publisher that persists the full covenant report in PostgreSQL."""

    def __init__(self, repository: ReportRepository) -> None:
        """Initialize with report repository dependency."""
        self._repository = repository

    def publish(self, report: CovenantReport) -> PublicationResult:
        """Persist report and return database identifier as reference."""
        report_id = self._repository.save_report(report)
        return PublicationResult(success=True, reference=str(report_id))
