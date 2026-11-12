"""
verifier for work-in-progress code to test functionality
"""

from datetime import date, time

from filters import FilterPipeline
from models import Company, FareCondition, Offer, TravelerProfile, Booking
from pathlib import Path
from loader import load_companies, load_offers, save_rejected_records
from scoring import ScoringEngine
from recommender import PresetProfiles, RecommendationExplainer

"""
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
"""
"""
##### START LOADER.PY TEST #####
# NOTE: this requires a .csv file to already exist in the data folder
rejected_records = []

# load companies and offers from CSV files
companies = load_companies(Path("data/companies.csv"), rejected_records)
offers = load_offers(Path("data/offers.csv"), companies, rejected_records)

print(f"Loaded Companies : {len(companies)}")
print(f"Loaded Offers : {len(offers)}")
print(f"Rejected Rows : {len(rejected_records)}")

# export error log
save_rejected_records(rejected_records, Path("output"))

##### END LOADER.PY TEST #####
"""

"""
##### START FILTERS.PY TEST #####
# 1. create company and fare terms
company = Company("COMP-SOL01", "SolRuta", "express")
fare_standard = FareCondition(is_changeable=False, is_refundable=False)
fare_flex = FareCondition(is_changeable=True, is_refundable=False)

# 2. create sample offers
offers = [
    # valid offer
    Offer("OFF-MAD-BCN-001", company, "Madrid", "Barcelona", date(2026, 7, 12), time(8, 0), time(14, 0), 360, 35.0, 0, 10, 4.5, 15.0, fare_standard),

    # over budget offer
    Offer("OFF-MAD-BCN-002", company, "Madrid", "Barcelona", date(2026, 7, 12), time(10, 0), time(16, 0), 360, 65.0, 0, 10, 4.8, 14.0, fare_flex),

    # wrong destination
    Offer("OFF-MAD-VAL-003", company, "Madrid", "Valencia", date(2026, 7, 12), time(9, 0), time(13, 0), 240, 25.0, 0, 10, 4.0, 10.0, fare_standard),

    # insufficient seats
    Offer("OFF-MAD-BCN-004", company, "Madrid", "Barcelona", date(2026, 7, 12), time(14, 0), time(20, 0), 360, 30.0, 0, 1, 4.2, 15.0, fare_standard),
]

# 3. define traveler profile with budget cap of EUR 40 and 2 seats required
profile = TravelerProfile(
    name="Carlos Ruiz",
    origin="Madrid",
    destination="Barcelona",
    start_date=date(2026, 7, 10),
    end_date=date(2026, 7, 15),
    max_budget=40.0,
    required_seats=2
)

# 4. run pipeline
pipeline = FilterPipeline()
eligible, disqualified = pipeline.filter_offers(offers, profile)

print(f"Total offers in         : {len(offers)}")
print(f"Eligible offers out     : {len(eligible)} ({[o.offer_id for o in eligible]}")
print(f"Disqualified offers out : {len(disqualified)}")

for offer, filter_name, reason in disqualified:
    print(f" - [{offer.offer_id}] failed '{filter_name}': {reason}")
"""


##### START SCORING.PY MODULE (+ RECOMMENDER.PY) #####
# 1. setup sample companies and fare terms
solruta = Company("COMP-SOL01", "SolRuta", "low_cost", fleet_rating=4.2, eco_certified=True)
camino = Company("COMP-CAM02", "Camino Express", "express", fleet_rating=4.7, eco_certified=False)

fare_nonflex = FareCondition(is_changeable=False, is_refundable=False)
fare_flex = FareCondition(is_changeable=True, is_refundable=True, change_fee_eur=0.0)

offers = [
    # offer A
    Offer("OFF-MAD-BCN-101", solruta, "Madrid", "Barcelona", date(2026, 7, 12), time(8, 0), time(14, 30), 390, 29.50, 0, 15, 4.3, 14.5, fare_nonflex),
    # offer B
    Offer("OFF-MAD-BCN-102", camino, "Madrid", "Barcelona", date(2026, 7, 12), time(9, 15), time(14, 45), 330, 48.00, 0, 20, 4.8, 18.0, fare_flex),
]

# 2. get preset profiles
budget_user = PresetProfiles.budget_traveler()
biz_user = PresetProfiles.business_traveler()

# 3. Score and explanation
engine = ScoringEngine()
explainer = RecommendationExplainer()

# evaluate budget user
budget_scored = engine.score_offers(offers, budget_user)
print(explainer.format_full_recommendation_report(budget_scored, budget_user))

