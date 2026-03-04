"""Normalized asset value object."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class NormalizedAsset:
    """Canonical asset representation used by the domain layer."""

    asset_id: str
    status: str
    is_eligible: bool

    outstanding_amount: Optional[Decimal] = None
    interest_rate_percentage: Optional[Decimal] = None
    loan_status: Optional[str] = None

    outstanding_principal_amount: Optional[Decimal] = None
    total_principal_amount: Optional[Decimal] = None
    total_fee_amount: Optional[Decimal] = None
    created_at: Optional[date] = None
    due_date: Optional[date] = None

    advance_amount: Optional[Decimal] = None
    fee_percentage: Optional[Decimal] = None
    origination_date: Optional[date] = None
    maturity_date: Optional[date] = None
