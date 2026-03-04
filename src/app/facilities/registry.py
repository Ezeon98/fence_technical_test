"""Facility strategy registry."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.ports.facility_strategy import (
    EffectiveRateStrategy,
    EligibilityStrategy,
    FacilityMapper,
)
from app.facilities.facility_alpha.eligibility import FacilityAlphaEligibility
from app.facilities.facility_alpha.mapper import FacilityAlphaMapper
from app.facilities.facility_alpha.rate_strategy import FacilityAlphaRateStrategy
from app.facilities.facility_beta.eligibility import FacilityBetaEligibility
from app.facilities.facility_beta.mapper import FacilityBetaMapper
from app.facilities.facility_beta.rate_strategy import FacilityBetaRateStrategy


@dataclass(frozen=True)
class FacilityBundle:
    """Facility strategy bundle."""

    mapper: FacilityMapper
    eligibility: EligibilityStrategy
    rate_strategy: EffectiveRateStrategy
    covenant_threshold: Decimal


def get_facility_bundle(facility_id: str) -> FacilityBundle:
    """Resolve a facility strategy bundle by identifier."""
    mapping: dict[str, FacilityBundle] = {
        "facility_alpha": FacilityBundle(
            mapper=FacilityAlphaMapper(),
            eligibility=FacilityAlphaEligibility(),
            rate_strategy=FacilityAlphaRateStrategy(),
            covenant_threshold=Decimal("12.00"),
        ),
        "facility_beta": FacilityBundle(
            mapper=FacilityBetaMapper(),
            eligibility=FacilityBetaEligibility(),
            rate_strategy=FacilityBetaRateStrategy(),
            covenant_threshold=Decimal("10.50"),
        ),
    }
    if facility_id not in mapping:
        raise ValueError(f"Unknown facility_id: {facility_id}")
    return mapping[facility_id]
