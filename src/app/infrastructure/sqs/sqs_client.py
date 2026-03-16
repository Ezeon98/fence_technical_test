"""Thin SQS client wrapper to isolate boto3 integration details."""

from __future__ import annotations

from typing import Any

import boto3


class SqsClient:
    """Adapter for SQS queue operations required by the API layer."""

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
    ) -> None:
        """Build a boto3 SQS client from explicit environment-backed settings."""
        client_kwargs: dict[str, str] = {
            "service_name": "sqs",
            "region_name": region_name,
        }
        if aws_access_key_id:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self._client = boto3.client(**client_kwargs)

    def receive_messages(
        self,
        queue_url: str,
        max_number: int = 10,
        wait_time_seconds: int = 2,
    ) -> list[dict[str, Any]]:
        """Read up to max_number messages from the configured source queue."""
        response = self._client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_number,
            WaitTimeSeconds=wait_time_seconds,
        )
        return response.get("Messages", [])

    def send_message(self, queue_url: str, message_body: str) -> str | None:
        """Send a single message to a queue and return the message id if present."""
        response = self._client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
        )
        return response.get("MessageId")

    def delete_message(self, queue_url: str, receipt_handle: str) -> None:
        """Delete a processed message from the source queue."""
        self._client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle,
        )
