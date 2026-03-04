"""Unit tests for deterministic basis-point conversion."""

from decimal import Decimal

from app.infrastructure.hash.canonical_hash import effective_rate_to_bps


def test_effective_rate_to_bps_uses_two_decimal_rate() -> None:
    """Ensure basis-point conversion uses two-decimal rounded percentage."""
    rate = Decimal("18.54")

    result = effective_rate_to_bps(rate)

    assert result == 1854


def test_effective_rate_to_bps_rounds_half_up() -> None:
    """Ensure half-up rounding is applied before bps conversion."""
    rate = Decimal("10.555")

    result = effective_rate_to_bps(rate)

    assert result == 1056
