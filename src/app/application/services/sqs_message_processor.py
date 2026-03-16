"""Service for polling SQS and processing covenant messages."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from app.application.services.covenant_processing_service import (
    CovenantProcessingService,
)
from app.infrastructure.sqs.sqs_client import SqsClient

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SqsProcessingSummary:
    """Outcome counters for one SQS processing batch."""

    polled_messages: int
    processed_successfully: int
    sent_to_dlq: int
    errors: list[str]


class SqsMessageProcessor:
    """Poll, validate, process, and route failed messages to the DLQ."""

    def __init__(
        self,
        sqs_client: SqsClient,
        covenant_processing_service: CovenantProcessingService,
        queue_url: str,
        dlq_url: str,
    ) -> None:
        """Initialize message processor with SQS and covenant dependencies."""
        self._sqs_client = sqs_client
        self._covenant_processing_service = covenant_processing_service
        self._queue_url = queue_url
        self._dlq_url = dlq_url

    def process_messages(self) -> SqsProcessingSummary:
        """Process one polling batch from source queue and return counters."""
        messages = self._sqs_client.receive_messages(queue_url=self._queue_url)
        processed_successfully = 0
        sent_to_dlq = 0
        errors: list[str] = []

        LOGGER.info("Polled %s message(s) from SQS source queue.", len(messages))

        for message in messages:
            was_processed, was_sent_to_dlq, error = self._process_single_message(
                message
            )
            if was_processed:
                processed_successfully += 1
            if was_sent_to_dlq:
                sent_to_dlq += 1
            if error is not None:
                errors.append(error)

        return SqsProcessingSummary(
            polled_messages=len(messages),
            processed_successfully=processed_successfully,
            sent_to_dlq=sent_to_dlq,
            errors=errors,
        )

    def _process_single_message(
        self, message: dict[str, Any]
    ) -> tuple[bool, bool, str | None]:
        """Process one SQS message and return status flags and optional error."""
        receipt_handle = message.get("ReceiptHandle")
        body = message.get("Body")

        if receipt_handle is None or body is None:
            error = "SQS message missing ReceiptHandle or Body"
            LOGGER.error(error)
            return False, False, error

        payload, parse_error = self._parse_payload(body)
        if parse_error is not None:
            return self._reject_message(
                body=body,
                receipt_handle=receipt_handle,
                rejection_reason=parse_error,
            )

        validation_error = self._validate_payload(payload)
        if validation_error is not None:
            return self._reject_message(
                body=body,
                receipt_handle=receipt_handle,
                rejection_reason=validation_error,
            )

        try:
            self._covenant_processing_service.process(
                facility_id=str(payload["facility_id"]),
                as_of_date=date.fromisoformat(str(payload["as_of_date"])),
                portfolio_json=payload["portfolio_json"],
            )
            self._sqs_client.delete_message(
                queue_url=self._queue_url,
                receipt_handle=receipt_handle,
            )
            return True, False, None
        except Exception as error:  # pragma: no cover - defensive runtime path
            rejection_reason = f"processing_error: {error}"
            return self._reject_message(
                body=body,
                receipt_handle=receipt_handle,
                rejection_reason=rejection_reason,
            )

    def _parse_payload(
        self, body: str
    ) -> tuple[dict[str, Any], str | None] | tuple[None, str]:
        """Parse message body as JSON object or return an explicit reason."""
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return None, "invalid_json"

        if not isinstance(payload, dict):
            return None, "payload_must_be_json_object"

        return payload, None

    def _validate_payload(self, payload: dict[str, Any]) -> str | None:
        """Validate required top-level and assets structure for covenant flow."""
        facility_id = payload.get("facility_id")
        if not isinstance(facility_id, str) or not facility_id.strip():
            return "missing_or_invalid_facility_id"

        as_of_date_raw = payload.get("as_of_date")
        if not isinstance(as_of_date_raw, str):
            return "missing_or_invalid_as_of_date"

        try:
            date.fromisoformat(as_of_date_raw)
        except ValueError:
            return "invalid_as_of_date_format"

        portfolio_json = payload.get("portfolio_json")
        if not isinstance(portfolio_json, dict):
            return "missing_or_invalid_portfolio_json"

        assets = portfolio_json.get("assets")
        if not isinstance(assets, list):
            return "missing_or_invalid_assets"

        if any(not isinstance(asset, dict) for asset in assets):
            return "invalid_asset_item"

        return None

    def _reject_message(
        self,
        body: str,
        receipt_handle: str,
        rejection_reason: str,
    ) -> tuple[bool, bool, str]:
        """Forward rejected message to DLQ and remove source message on success."""
        dlq_payload = {
            "original_message": body,
            "rejection_reason": rejection_reason,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

        try:
            self._sqs_client.send_message(
                queue_url=self._dlq_url,
                message_body=json.dumps(dlq_payload),
            )
            self._sqs_client.delete_message(
                queue_url=self._queue_url,
                receipt_handle=receipt_handle,
            )
            LOGGER.warning("Message rejected and sent to DLQ: %s", rejection_reason)
            return False, True, rejection_reason
        except Exception as error:  # pragma: no cover - defensive runtime path
            failure_reason = f"dlq_publish_error: {error}"
            LOGGER.exception("Failed to publish message to DLQ.")
            return False, False, failure_reason
