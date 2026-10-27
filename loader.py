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



# export logged rejected records to output file
def save_rejected_records(rejected_records: List[RejectedRecord], output_dir: Path) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    target_file = out_path / "rejected_records.txt"

    """
    with open(target_file, "w", newline="") as csvfile:
    ** formatting goes here **
    """

