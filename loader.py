"""
Handles file reading (CSV/JSON), data parsing, object instantiation,
and logging corrupted records to output/rejected_records.txt
"""

import csv
import json
from datetime import datetime, date, time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from exceptions import DataNotFoundError, InvalidIdentifierError, InvalidRecordError
from models import Company, FareCondition, Offer
from validators import(
    validate_company_id,
    validate_offer_id,
    validate_offer_numeric_bounds
)

# encapsulates metadata for a rejected CSV row during parsing
class RejectedRecord:
    def __init__(self, filename: str, row_number: int, field: str, reason: str, raw_line: str = ""):
        self.filename = filename
        self.row_number = row_number
        self.field = field
        self.reason = reason
        self.raw_line = raw_line

    def __str__(self) -> str:
        return f"[{self.filename}: Row {self.row_number}] Field '{self.field}' rejected: {self.reason}"

    def __repr__(self) -> str:
        return self.__str__()

    """
    expected CSV columns should at least be:
    company_id, name, profile_type, fleet_rating, eco_certified.
    """



def load_companies(file_path: Path, rejected_records: List[RejectedRecord]) -> Dict[str, Company]:
    companies = {}
    path = Path(file_path)

    if not path.exists():
        raise DataNotFoundError(f"Companies file not found: {path}")

    with open(path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=2):
            try:
                c_id = row.get("company_id", "").strip()
                name = row.get("name", "").strip()
                p_type = row.get("profile_type", "").strip()
                rating_str = row.get("fleet_rating", "4.0").strip()
                eco_str = row.get("eco_certified", "false").strip().lower()

                validate_company_id(c_id)
                fleet_rating = float(rating_str)
                eco_certified = eco_str in ("true", "1", "yes")

                company = Company(
                    company_id=c_id,
                    name=name,
                    profile_type=p_type,
                    fleet_rating=fleet_rating,
                    eco_certified=eco_certified
                )
                companies[c_id] = company
            except (InvalidIdentifierError, InvalidRecordError, ValueError) as e:
                rejected_records.append(
                    RejectedRecord(path.name, row_idx, "company_id/rating", str(e), str(row))
                )
    return companies

# reads offers CSV file
def load_offers(
        file_path: Path,
        companies: Dict[str, Company],
        rejected_records: List[RejectedRecord],
) -> List[Offer]:
    offers = []
    path = Path(file_path)

    if not path.exists():
        raise DataNotFoundError(f"Offers file not found: {path}")

    with open(path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=2):
            try:
                offer_id = row.get("offer_id", "").strip()
                company_id = row.get("company_id", "").strip()
                origin = row.get("origin", "").strip()
                destination = row.get("destination", "").strip()

                # regex validation
                validate_offer_id(offer_id)

                # company lookup
                if company_id not in companies:
                    raise InvalidRecordError(f"Unknown company_id '{company_id}' not found in company profiles")
                company = companies[company_id]

                # date and time parsing
                travel_date = datetime.strptime(row.get("travel_date", "").strip(), "%Y-%m-%d").date()
                dep_time = datetime.strptime(row.get("departure_time", "").strip(), "%H:%M:%S").time()
                arr_time = datetime.strptime(row.get("arrival_time", "").strip(), "%H:%M:%S").time()

                # numeric type conversions
                duration = int(row.get("duration_minutes", 0))
                price = float(row.get("price", -1.0))
                transfers = int(row.get("transfers", 0))
                seats = int(row.get("available_seats", 0))
                rating = float(row.get("customer_rating", 0.0))
                emissions = float(row.get("co2_emissions_kg", 0.0))

                # operational bounds
                if not validate_offer_numeric_bounds(price, duration, transfers, seats, rating, emissions):
                    raise InvalidRecordError("Offer failed operational bounds check")

                # fare condition parsing
                is_changeable = row.get("is_changeable", False).strip().lower() in ("true", "1", "yes")
                is_refundable = row.get("is_refundable", False).strip().lower() in ("true", "1", "yes")
                luggage_kg = float(row.get("luggage_kg", 20.0))
                change_fee = float(row.get("change_fee_eur", 0.0))

                fare = FareCondition(
                    is_changeable=is_changeable,
                    is_refundable=is_refundable,
                    luggage_kg=luggage_kg,
                    change_fee_eur=change_fee,
                )

                # construct domain offer object
                offer = Offer(
                    offer_id=offer_id,
                    company=company,
                    origin=origin,
                    destination=destination,
                    travel_date=travel_date,
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    duration_minutes=duration,
                    price=price,
                    transfers=transfers,
                    available_seats=seats,
                    customer_rating=rating,
                    co2_emissions_kg=emissions,
                    fare_condition=fare,
                )
                offers.append(offer)

            except (InvalidIdentifierError, InvalidRecordError, ValueError, KeyError) as e:
                rejected_records.append(
                    RejectedRecord(path.name, row_idx, "offer_data", str(e), str(row))
                )
    return offers


# export logged rejected records to output file
def save_rejected_records(rejected_records: List[RejectedRecord], output_dir: Path) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    target_file = out_path / "rejected_records.txt"

    with open(target_file, mode="w", encoding="utf-8", newline="") as f:
        f.write("===========================================================\n")
        f.write("           BUSBIDDER SPAIN - REJECTED RECORDS LOG          ")
        f.write("===========================================================\n\n")
        if not rejected_records:
            f.write("No rejected records found\n")
        else:
            for rec in rejected_records:
                f.write(f"{rec}\n")
    return target_file
