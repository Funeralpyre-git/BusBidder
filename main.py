"""
main executable
verifier for work-in-progress code to test functionality
"""

import argparse
import sys
from pathlib import Path
from typing import List

from exceptions import BusBidderError, DataNotFoundError
from loader import load_companies, load_offers, save_rejected_records, RejectedRecord
from filters import FilterPipeline
from scoring import ScoringEngine
from recommender import PresetProfiles, RecommendationExplainer
from booking import BookingManager

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
"""

"""
##### START BOOKING.PY MODULE #####
# 1. setup sample carrier and offer with 5 available seats
solruta = Company("COMP-SOL01", "SolRuta", "express")
fare = FareCondition(is_changeable=True, is_refundable=False)
offer = Offer(
    "OFF-MAD-BCN-101", solruta, "Madrid", "Barcelona",
    date(2026, 7, 12), time(8, 30), time(14, 30), 360,
    35.00, 0, available_seats=5, customer_rating=4.5,
    co2_emissions_kg=15.0, fare_condition=fare
)

# 2. setup traveler requiring 2 seats
traveler = TravelerProfile(
    "Lucia Gomez", "Madrid", "Barcelona",
    date(2026, 7, 10), date(2026, 7, 15), required_seats=2
)

# 3. instantiate managed and execute booking
manager = BookingManager(output_dir=Path("output"))

print(f"Seats BEFORE booking : {offer.available_seats}") # should output 5
booking = manager.create_booking(offer, traveler)
print(f"Seats AFTER booking : {offer.available_seats}") # should output 3

print("\nGenerated Booking Reference: ", booking.booking_reference)
print(booking.summary())
"""

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="BusBidder Spain - Bus ranking platform"
    )

    parser.add_argument(
        "--companies",
        type=str,
        default="/data/companies.csv",
        help="Path to offers CSV file (default: data/companies.csv)"
    )

    parser.add_argument(
        "--offers",
        type=str,
        default="/data/offers.csv",
        help="Path to offers CSV file (default: data/offers.csv)"
    )

    parser.add_argument(
        "--profile",
        type=str,
        choices=["budget", "business", "comfort", "eco"],
        default="budget",
        help="Select preset traveler profile (budget, business, comfort, eco)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Target output directory (default: output)"
    )

    parser.add_argument(
        "--book",
        action="store_true",
        help="Automatically execute reservation for top recommended offer"
    )

    return parser.parse_args()

# instantiates the specified traveler preset
def get_profile_by_name(profile_name: str):
    if profile_name == "business":
        return PresetProfiles.business_traveler()
    elif profile_name == "comfort":
        return PresetProfiles.comfort_tourist()
    elif profile_name == "eco":
        return PresetProfiles.eco_traveler()
    else:
        return PresetProfiles.budget_traveler()

# saves formatted recommendation report to file
def write_recommendation_report(report_text: str, output_dir: Path) -> Path:
    target_file = output_dir / "recommendation_report.txt"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    return target_file

def main():
    args = parse_arguments()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    rejected_records: List[RejectedRecord] = []

    print("=======================================")
    print("     BUSBIDDER SPAIN - PROCESSING      ")
    print("=======================================")

    try:
        # 1. ingest data files
        companies_path = Path(args.companies)
        offers_path = Path(args.offers)

        print(f"Loading companies from: {companies_path}")
        companies = load_companies(companies_path, rejected_records)

        print(f"Loading offers from   : {offers_path}")
        offers = load_offers(offers_path, companies, rejected_records)

        # 2. load selected traveler profile
        profile = get_profile_by_name(args.profile)
        print(f"Active profile: {profile}")
        print(f"Route         : {profile.origin} -> {profile.destination} ({profile.start_date} to {profile.end_date})")

        # 3. filtering engine
        pipeline = FilterPipeline()
        eligible_offers, disqualified = pipeline.filter_offers(offers, profile)

        # 4. scoring engine
        scoring_engine = ScoringEngine()
        scored_offers = scoring_engine.score_offers(eligible_offers, profile)

        # 5. recommendation generator
        explainer = RecommendationExplainer()
        report_text = explainer.format_full_recommendation_report(scored_offers, profile)
        report_file = write_recommendation_report(report_text, output_dir)

        # 6. execute reservation
        booking_ref = "N/A"
        if scored_offers and (args.book or True):
            booking_mgr = BookingManager(output_dir=output_dir)
            top_pick = scored_offers[0].offer
            confirmed_booking = booking_mgr.create_booking(top_pick, profile)
            booking_ref = confirmed_booking.booking_reference

        # 7. export rejected records log
        rejected_file = save_rejected_records(rejected_records, output_dir)

        # 8. console summary
        print("\n=======================================================")
        print("     BUSBIDDER SPAIN - EXECUTION COMPLETION SUMMARY     ")
        print("========================================================")
        print(f"Total Offers Ingested   : {len(offers)}")
        print(f"Eligible Offers         : {len(eligible_offers)}")
        print(f"Disqualified Offers     : {len(disqualified)}")
        print(f"Rejected Rows           : {len(rejected_records)}")
        if scored_offers:
            print(f"Top Recommendation  : {scored_offers[0].offer.offer_id} ({scored_offers[0].offer.company.name})")
            print(f"Top Composite Score : {scored_offers[0].total_score:.1f} / 100.0")
            print(f"Confirmed Booking Ref : {booking_ref}")
        else:
            print("Top Recommendation : None (No eligible offers matched)")
        print("------------------------------------------------------")
        print("Created Output Files:")
        print(f"    - {report_file}")
        print(f"    - {rejected_file}")
        print(f"    - {output_dir / 'bookings.csv'}")
        print(f"    - {output_dir / 'booking_receipts.txt'}")
        print("======================================================")

    except DataNotFoundError as e:
        print(f"\n[ERROR] Missing Input File: {e}", file=sys.stderr)
        sys.exit(1)
    except BusBidderError as e:
        print(f"\n[ERROR] Domain Execution Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR]: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()