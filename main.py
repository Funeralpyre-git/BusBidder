"""
verifier for work-in-progress code to test functionality
"""

from datetime import date, time
from models import Company, FareCondition, Offer, TravelerProfile, Booking

##### START MODELS.PY TEST #####

# Test 1. Instantiate Company and Fare
solruta = Company("SOL-01", "SolRuta", "low_cost", fleet_rating=4.2)
fare = FareCondition(is_changeable=True, is_refundable=False, change_fee_eur=5.0)

# Test 2. Offer
offer = Offer(
    offer_id="OFF-MAD-BCN-001",
    company=solruta,
    origin="Madrid",
    destination="Barcelona",
    travel_date=date(2026, 7, 12),
    departure_time=time(8, 30),
    arrival_time=time(16, 0),
    duration_minutes=450,
    price=32.5,
    transfers=0,
    available_seats=15,
    customer_rating=4.3,
    co2_emissions_kg=18.2,
    fare_condition=fare
)

# Test 3. Instantiate Traveler
traveler = TravelerProfile(
    name="Elena Ramos",
    origin="Madrid",
    destination="Barcelona",
    start_date=date(2026, 7, 12),
    end_date=date(2026, 7, 14),
    max_budget=50.0,
    required_seats=2
)

# Test 4. Reserve seats & create booking
offer.decrement_seats(traveler.required_seats)
booking = Booking("BB-MAD-109283", offer, traveler, num_seats=traveler.required_seats)

print(booking.summary())
print(f"Remaining seats after booking: {offer.available_seats}") #should return 13

##### END MODELS.PY TEST #####