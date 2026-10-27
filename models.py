"""
Marketplace representations including: Company, FareCondition, Offer, TravelerProfile, and Booking
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Dict, Optional

@dataclass(frozen=True)
class Company:
    company_id: str
    name: str
    profile_type: str
    fleet_rating: float= 4.0
    eco_certified: bool = False

    def __post_init__(self):
        if not self.company_id or not self.name:
            raise ValueError("Company ID and Name must not be empty.")
        if not (1.0 <= self.fleet_rating <= 5.0):
            raise ValueError("Fleet rating {self.fleet_rating} must be between 0 and 5.0.")

@dataclass(frozen=True)
class FareCondition:
    is_changeable: bool
    is_refundable: bool
    luggage_kg: float = 20.0
    change_fee_eur: float = 0.0

    def flexibility_score(self) -> float:
        score = 0.0
        if self.is_changeable:
            score += 50.0 - min(self.change_fee_eur * 2.0, 30.0)
        if self.is_refundable:
            score += 50.0
        return max(0.0, score)

class Offer:
    def __init__(
        self,
        offer_id: str,
        company: Company,
        origin: str,
        destination: str,
        travel_date: date,
        departure_time: time,
        arrival_time: time,
        duration_minutes: int,
        price: float,
        transfers: int,
        available_seats: int,
        customer_rating: float,
        co2_emissions_kg: float,
        fare_condition: FareCondition
    ):
        if not offer_id or not isinstance(offer_id, str):
            raise ValueError("Offer ID must be a non-empty string.")
        if not isinstance(company, Company):
            raise ValueError("Company must be an instance of Company.")
        if not isinstance(fare_condition, FareCondition):
            raise ValueError("fare_condition must be an instance of FareCondition.")
        if price < 0.0:
            raise ValueError("Price cannot be negative.")
        if duration_minutes <= 0:
            raise ValueError("Duration minutes cannot be negative.")
        if transfers < 0:
            raise ValueError("Transfers cannot be negative.")
        if not (0.0 <= customer_rating <= 5.0):
            raise ValueError(f"Customer rating {customer_rating} must be between 0 and 5.0.")
        if available_seats < 0:
            raise ValueError("Available seats cannot be negative.")

        self.offer_id = offer_id.strip()
        self.company = company
        self.origin = origin.strip().title()
        self.destination = destination.strip().title()
        self.travel_date = travel_date
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.duration_minutes = duration_minutes
        self.price = float(price)
        self.transfers = transfers
        self.customer_rating = float(customer_rating)
        self.c02_emissions_kg = float(co2_emissions_kg)
        self.fare_condition = fare_condition

        # protected state for inventory management
        self._available_seats = int(available_seats)

    @property
    def available_seats(self) -> int:
        return self._available_seats

    def decrement_seats(self, count: int = 1) -> None:
        if count <= 0:
            raise ValueError("Seat reservation count must be at least 1.")
        if count > self._available_seats:
            raise ValueError(f"Cannot reserve {count} seats. Only {self._available_seats} remaining.")
        self._available_seats -= count

    def departure_minutes_from_midnight(self) -> int:
        return self.departure_time.hour * 60 + self.departure_time.minute

    def __repr__(self) -> str:
        return(
            f"Offer({self.offer_id}, {self.company}, {self.origin} -> {self.destination}, "
            f"EUR {self.price:.2f}, {self.duration_minutes}m, seats={self._available_seats})"
        )

class TravelerProfile:
    DEFAULT_WEIGHTS = {
        "price": 0.40,
        "duration": 0.25,
        "departure_convenience": 0.15,
        "flexibility": 0.20,
    }

    def __init__(
            self,
            name: str,
            origin: str,
            destination: str,
            start_date: date,
            end_date: date,
            max_budget: Optional[float] = None,
            preferred_departure_time: Optional[time] = None,
            max_transfers: Optional[int] = None,
            required_seats: int = 1,
            requires_changeable: bool = False,
            requires_refundable: bool = False,
            weights: Optional[Dict[str, float]] = None
    ):
        if not name or not origin or not destination:
            raise ValueError("Traveler name, origin, and destination cannot be empty.")
        if end_date < start_date:
            raise ValueError("End date cannot precede start date.")
        if required_seats < 1:
            raise ValueError("Required seats cannot be less than 1.")

        self.name = name.strip()
        self.origin = origin.strip().title()
        self.destination = destination.strip().title()
        self.start_date = start_date
        self.end_date = end_date
        self.max_budget = float(max_budget) if max_budget is not None else None
        self.preferred_departure_time = preferred_departure_time or time(9, 0)
        self.max_transfers = max_transfers
        self.required_seats = required_seats
        self.requires_changeable = requires_changeable
        self.requires_refundable = requires_refundable

        # validate and store preference weights
        self._weights = self._validate_weights(weights or self.DEFAULT_WEIGHTS)

    @property
    def weights(self) -> Dict[str, float]:
        return self._weights.copy()

    @staticmethod
    def _validate_weights(weights: Dict[str, float]) -> Dict[str, float]:
        if not weights:
            raise ValueError("Weights cannot be empty.")
        for k, v in weights.items():
            if v < 0:
                raise ValueError(f"Weight for '{k}' cannot be negative.")
        total = sum(weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Criteria weights must sum to 1.0 (100%), got {total:.4f}.")
        return {k: float(v) for k, v in weights.items()}

    def __repr__(self) -> str:
        return(
            f"TravelerProfile({self.name}, {self.origin}->{self.destination}, "
            f"Budget={self.max_budget}, Window={self.start_date} to {self.end_date})"
        )

class Booking:
    def __init__(
            self,
            booking_reference: str,
            offer: Offer,
            traveler: TravelerProfile,
            num_seats: int = 1,
            booking_timestamp: Optional[datetime] = None,
            status: str = "CONFIRMED"
    ):
        if not booking_reference:
            raise ValueError("Booking reference cannot be empty.")
        if num_seats <= 0:
            raise ValueError("Number of seats must be at least 1.")

        self.booking_reference = booking_reference
        self.offer = offer
        self.traveler = traveler
        self.num_seats = num_seats
        self.total_price = round(offer.price * num_seats, 2)
        self.booking_timestamp = booking_timestamp or datetime.now()
        self.status = status

    def summary(self) -> str:
        return(
            f"--- BOOKING CONFIRMATION: {self.booking_reference} ---\n"
            f"Passenger         : {self.traveler.name}\n"
            f"Route             : {self.offer.origin} -> {self.offer.destination}\n"
            f"Carrier           : {self.offer.company.name} ({self.offer.company.profile_type})\n"
            f"Date & Departure  : {self.offer.travel_date} at {self.offer.departure_time.strftime('%H:%M')}\n"
            f"Seats Reserved    : {self.num_seats} (Total: EUR {self.total_price:.2f})\n"
            f"Flexibility       : Changeable={self.offer.fare_condition.is_changeable}, "
            f"Refundable={self.offer.fare_condition.is_refundable}\n"
            f"Status            : {self.status}\n"
            f"------------------------------------------------"
        )









