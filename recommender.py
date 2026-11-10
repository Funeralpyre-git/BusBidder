"""
recommendation generator and preset profiles
"""

from datetime import date, time
from typing import List, Dict, Optional
from models import TravelerProfile
from scoring import ScoredOffer

class PresetProfiles:
    @staticmethod
    def budget_traveler(
            name: str = "Ana (Budget)",
            origin: str = "Madrid",
            destination: str = "Barcelona",
            start_date: date = date(2026, 7, 12),
            end_date: date = date(2026, 7, 15),
            max_budget: float = 40.0
    ) -> TravelerProfile:
        return TravelerProfile(
            name=name,
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            max_budget=max_budget,
            weights={
                "price": 0.60,
                "duration": 0.20,
                "departure_convenience": 0.10,
                "flexibility": 0.10,
            }
        )

    @staticmethod
    def business_traveler(
            name: str = "Carlos (Business)",
            origin: str = "Madrid",
            destination: str = "Barcelona",
            start_date: date = date(2026, 7, 12),
            end_date: date = date(2026, 7, 15),
            preferred_time: time = time(8, 0)
    ) -> TravelerProfile:
        return TravelerProfile(
            name=name,
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            preferred_departure_time=preferred_time,
            requires_changeable=True,
            weights={
                "duration": 0.40,
                "flexibility": 0.30,
                "departure_convenience": 0.20,
                "price": 0.10,
            }
        )