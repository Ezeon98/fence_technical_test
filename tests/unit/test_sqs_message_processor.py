"""Unit tests for SQS message processing and rejection flow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.application.services.sqs_message_processor import SqsMessageProcessor


@dataclass
class FakeSqsClient:
    """In-memory SQS client double used by processor tests."""

    messages: list[dict[str, Any]]

    def __post_init__(self) -> None:
        """Initialize operation tracking collections for assertions."""
        self.sent_to_dlq: list[tuple[str, str]] = []
        self.deleted_messages: list[tuple[str, str]] = []

    def receive_messages(
        self,
        queue_url: str,
        max_number: int = 10,
        wait_time_seconds: int = 2,
    ) -> list[dict[str, Any]]:
        """Return predefined messages for one processing batch."""
        _ = (queue_url, max_number, wait_time_seconds)
        return self.messages

    def send_message(self, queue_url: str, message_body: str) -> str | None:
        """Record DLQ message publication."""
        self.sent_to_dlq.append((queue_url, message_body))
        return "msg-id"

    def delete_message(self, queue_url: str, receipt_handle: str) -> None:
        """Record source queue message deletion."""
        self.deleted_messages.append((queue_url, receipt_handle))


@dataclass
class FakeCovenantProcessingService:
    """Test double for covenant processing service."""

    should_fail: bool = False

    def __post_init__(self) -> None:
        """Initialize call recorder for assertions."""
        self.calls: list[tuple[str, date, dict[str, Any]]] = []

    def process(
        self,
        facility_id: str,
        as_of_date: date,
        portfolio_json: dict[str, Any],
    ) -> dict[str, Any]:
        """Record payload and optionally raise to simulate failure."""
        self.calls.append((facility_id, as_of_date, portfolio_json))
        if self.should_fail:
            raise RuntimeError("simulated processing failure")
        return {}


def _build_processor(
    messages: list[dict[str, Any]],
    should_fail: bool = False,
) -> tuple[SqsMessageProcessor, FakeSqsClient, FakeCovenantProcessingService]:
    """Build a processor configured with deterministic in-memory doubles."""
    sqs_client = FakeSqsClient(messages=messages)
    processing_service = FakeCovenantProcessingService(should_fail=should_fail)
    processor = SqsMessageProcessor(
        sqs_client=sqs_client,
        covenant_processing_service=processing_service,
        queue_url="source-queue",
        dlq_url="dlq-queue",
    )
    return processor, sqs_client, processing_service


def test_valid_message_is_processed_and_deleted() -> None:
    """Ensure valid payload invokes processing service and deletes source item."""
    valid_payload = {
        "facility_id": "facility_educa",
        "as_of_date": "2026-03-04",
        "portfolio_json": {"assets": [{"external_id": "EDU-001"}]},
    }
    message = {
        "ReceiptHandle": "rh-1",
        "Body": json.dumps(valid_payload),
    }
    processor, sqs_client, processing_service = _build_processor([message])

    summary = processor.process_messages()

    assert summary.polled_messages == 1
    assert summary.processed_successfully == 1
    assert summary.sent_to_dlq == 0
    assert processing_service.calls[0][0] == "facility_educa"
    assert sqs_client.deleted_messages == [("source-queue", "rh-1")]
    assert sqs_client.sent_to_dlq == []


def test_invalid_json_goes_to_dlq_with_reason() -> None:
    """Ensure malformed JSON is rejected, sent to DLQ, and deleted from source."""
    message = {
        "ReceiptHandle": "rh-2",
        "Body": "{not-json}",
    }
    processor, sqs_client, processing_service = _build_processor([message])

    summary = processor.process_messages()

    assert summary.polled_messages == 1
    assert summary.processed_successfully == 0
    assert summary.sent_to_dlq == 1
    assert processing_service.calls == []
    assert sqs_client.deleted_messages == [("source-queue", "rh-2")]
    assert len(sqs_client.sent_to_dlq) == 1

    _, dlq_body = sqs_client.sent_to_dlq[0]
    dlq_payload = json.loads(dlq_body)
    assert dlq_payload["original_message"] == "{not-json}"
    assert dlq_payload["rejection_reason"] == "invalid_json"
    assert dlq_payload["timestamp"].endswith("Z")


def test_invalid_structure_goes_to_dlq() -> None:
    """Ensure invalid payload shape is rejected and no processing is attempted."""
    invalid_payload = {
        "as_of_date": "2026-03-04",
        "portfolio_json": {"assets": [{"external_id": "EDU-001"}]},
    }
    message = {
        "ReceiptHandle": "rh-3",
        "Body": json.dumps(invalid_payload),
    }
    processor, sqs_client, processing_service = _build_processor([message])

    summary = processor.process_messages()

    assert summary.polled_messages == 1
    assert summary.processed_successfully == 0
    assert summary.sent_to_dlq == 1
    assert processing_service.calls == []
    assert sqs_client.deleted_messages == [("source-queue", "rh-3")]

    _, dlq_body = sqs_client.sent_to_dlq[0]
    dlq_payload = json.loads(dlq_body)
    assert dlq_payload["rejection_reason"] == "missing_or_invalid_facility_id"


def test_processing_failure_goes_to_dlq() -> None:
    """Ensure runtime processing errors are captured and routed to DLQ."""
    valid_payload = {
        "facility_id": "facility_educa",
        "as_of_date": "2026-03-04",
        "portfolio_json": {"assets": [{"external_id": "EDU-001"}]},
    }
    message = {
        "ReceiptHandle": "rh-4",
        "Body": json.dumps(valid_payload),
    }
    processor, sqs_client, _ = _build_processor([message], should_fail=True)

    summary = processor.process_messages()

    assert summary.polled_messages == 1
    assert summary.processed_successfully == 0
    assert summary.sent_to_dlq == 1
    assert sqs_client.deleted_messages == [("source-queue", "rh-4")]

    _, dlq_body = sqs_client.sent_to_dlq[0]
    dlq_payload = json.loads(dlq_body)
    assert "processing_error" in dlq_payload["rejection_reason"]
