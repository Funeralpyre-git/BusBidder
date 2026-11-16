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