"""Publisher port definitions."""

from dataclasses import dataclass
from typing import Protocol

from app.domain.value_objects.covenant_report import CovenantReport


@dataclass(frozen=True)
class PublicationResult:
    """Represents the result of a publication attempt."""

    success: bool
    reference: str | None
    error_message: str | None = None


class Publisher(Protocol):
    """Port for publishing covenant outcomes to external stores."""

    def publish(self, report: CovenantReport) -> PublicationResult:
        """Publish a covenant report and return publication metadata."""
