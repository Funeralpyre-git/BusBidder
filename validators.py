"""
Regex & data validation rules
"""
import re
from datetime import date, time
from exceptions import InvalidIdentifierError

# regex patterns
COMPANY_ID_PATTERN = re.compile(r"^COMP-[A-Z0-9]{3,}$")
OFFER_ID_PATTERN = re.compile(r"^OFF-[A-Z]{3}-[A-Z]{3}-\d{3,}$")
BOOKING_REF_PATTERN = re.compile(r"^BB-[A-Z]{3}-\d{6}$")

# validates company identifier format
def validate_company_id(company_id: str) -> bool:
    if not isinstance(company_id, str) or not COMPANY_ID_PATTERN.match(company_id.strip()):
        raise InvalidIdentifierError(f"Invalid company ID format: '{company_id}. Expected format like 'COMP-SOL01'.")
    return True

# validates offer identifier format
def validate_offer_id(offer_id: str) -> bool:
    if not isinstance(offer_id, str) or not OFFER_ID_PATTERN.match(offer_id.strip()):
        raise InvalidIdentifierError(f"Invalid Offer ID format: '{offer_id}'. Expected format like 'OFF-MAD-BCN-101'.")
    return True

# validates booking reference format
def validate_booking_reference(ref: str) -> bool:
    if not isinstance(ref, str) or not BOOKING_REF_PATTERN.match(ref.strip()):
        raise InvalidIdentifierError(f"Invalid booking ref format: '{ref}'. Expected format like 'BB-MAD-849201'.")
    return True


def validate_offer_numeric_bounds(
        price: float,
        duration_minutes: int,
        transfers: int,
        available_seats: int,
        customer_rating: float,
        co2_emissions_kg: float
) -> bool:
    if price < 0.0:
        return False
    if duration_minutes <= 0:
        return False
    if transfers < 0:
        return False
    if available_seats < 0:
        return False
    if not (1.0 <= customer_rating <= 5.0):
        return False
    if co2_emissions_kg < 0.0:
        return False
    return True