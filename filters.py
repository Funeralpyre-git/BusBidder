##### Hard constraint filtering engine #####

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from models import Offer, TravelerProfile

# Defines the contract for evaluating whether an offer satisfies a profile constraint
class BaseFilter(ABC):
    @property
    @abstractmethod
    # returns human-readable name of the filter
    def name(self) -> str:
        pass

    @abstractmethod
    # evaluates an offer against a traveler profile
    def evaluate(self, offer: Offer, profile: TravelerProfile) -> Tuple[bool, str]:
        pass

# Enforces origin and destination route matching
class DestinationFilter(BaseFilter):
    @property
    def name(self) -> str:
        return "Destination and origin filter"

    def evaluate(self, offer: Offer, profile: TravelerProfile) -> Tuple[bool, str]:
        if offer.origin.lower() != profile.origin.lower():
            return (
                False,
                f"Origin mismatch: offer origin '{offer.origin}' does not match profile origin '{profile.origin}'"
            )
        if offer.destination.lower() != profile.destination.lower():
            return (
                False,
                f"Destination mismatch: offer destination '{offer.destination}' does not match profile destination '{profile.destination}'"
            )
        return (True, "")

# Enforces departure within the traveler's allowed travel date window
class TravelWindowFilter(BaseFilter):
    @property
    def name(self) -> str:
        return "Travel window filter"

    def evaluate(self, offer: Offer, profile: TravelerProfile) -> Tuple[bool, str]:
        if not (profile.start_date <= offer.travel_date <= profile.end_date):
            return (
                False,
                f"Travel date '{offer.travel_date}' is outside allowed window ({profile.start_date} - {profile.end_date})"
            )
        return (True, "")

# Enforces that total ticket price does not exceed the budget cap (if specified)
class BudgetFilter(BaseFilter):
    @property
    def name(self) -> str:
        return "Budget filter"

    def evaluate(self, offer: Offer, profile: TravelerProfile) -> Tuple[bool, str]:
        if profile.max_budget is not None and offer.price > profile.max_budget:
            return (
                False,
                f"Price EUR {offer.price:.2f} exceeds maximum budget ({profile.max_budget})"
            )
        return (True, "")

# enforces that available seats meet or exceed required passenger seats
class SeatAvailabilityFilter(BaseFilter):
    @property
    def name(self) -> str:
        return "Seat capacity filter"

    def evaluate(self, offer: Offer, profile: TravelerProfile) -> Tuple[bool, str]:
        if offer.available_seats < profile.required_seats:
            return (
                False,
                f"Insufficient seats: offer has {offer.available_seats} available, requires {profile.required_seats} seats"
            )
        return (True, "")

# enforces masimum allowed transfer limit (if specified)
class TransferFilter(BaseFilter):
    @property
    def name(self) -> str:
        return "Transfer filter"

    def evaluate(self, offer: Offer, profile: TravelerProfile) -> Tuple[bool, str]:
        if profile.max_transfers is not None and offer.transfers < profile.max_transfers:
            return (
                False,
                f"Transfers count ({offer.transfers}) exceeds maximum transfer count ({profile.max_transfers})"
            )
        return (True, "")

# enforces mandatory ticket changeability or refundability rules if requested
class FlexibilityFilter(BaseFilter):
    @property
    def name(self) -> str:
        return "Flexibility filter"

    def evaluate(self, offer: Offer, profile: TravelerProfile) -> Tuple[bool, str]:
        if profile.requires_changeable and not offer.fare_condition.is_changeable:
            return (
                False,
                "Ticket is non-changeable, but profile requires a changeable ticket"
            )
        if profile.requires_refundable and not offer.fare_condition.is_refundable:
            return (
                False,
                "Ticket is non-refundable, but profile requires a refundable ticket"
            )
        return (True, "")

# executes a chain of hard constraint filters sequentially.
# breaks upon the first failing filter and segregates offers into eligible and disqualified collections
class FilterPipeline:
    def __init__(self, filters: Optional[List[BaseFilter]] = None):
        self.filters = filters or [
            DestinationFilter(),
            TravelWindowFilter(),
            BudgetFilter(),
            SeatAvailabilityFilter(),
            TransferFilter(),
            FlexibilityFilter()
        ]

    # allows dynamic registration of additional hard constraint filters
    def add_filter(self, custom_filter: BaseFilter) -> None:
        if not isinstance(custom_filter, BaseFilter):
            raise TypeError("Filter must be of type BaseFilter")
        self.filters.append(custom_filter)

    def filter_offers(
            self,
            offers: List[Offer],
            profile: TravelerProfile,
    ) -> Tuple[List[Offer], List[Tuple[Offer, str, str]]]:
        eligible_offers: List[Offer] = []
        disqualified_offer: List[Tuple[Offer, str, str]] = []

        for offer in offers:
            passed_all = True
            for filter_obj in self.filters:
                satisfied, reason = filter_obj.evaluate(offer, profile)
                if not satisfied:
                    disqualified_offer.append((offer, filter_obj.name, reason))
                    passed_all = False
                    break

            if passed_all:
                eligible_offers.append(offer)
        return eligible_offers, disqualified_offer





