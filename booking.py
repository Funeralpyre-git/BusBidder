"""
booking management, inventory tracking and state persistence
handles seat capacity reservations, regex-compliant booking reference generation,
transaction receipts, and CSV file persistence
"""

import csv
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from exceptions import InvalidRecordError, InvalidIdentifierError
from models import Offer, TravelerProfile, Booking
from validators import validate_booking_reference

class BookingReferenceGenerator:

    @staticmethod
    def generate(origin: str) -> str:
        clean_origin = "".join(c for c in origin.upper() if c.isalpha())
        prefix = clean_origin[:3] if len(clean_origin) >= 3 else "ESP"
        digits = f"{random.randint(0, 999999):06d}"
        ref = f"BB-{prefix}-{digits}"

        # validation against regex rule before returning
        validate_booking_reference(ref)
        return ref

# manages booking reservations, seat inventory, and output file
class BookingManager:
    def __init__(self, output_dir: Path = Path("output")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.bookings_csv_path = self.output_dir / "bookings.csv"
        self.receipts_txt_path = self.output_dir / "booking_receipts.txt"
        self._confirmed_bookings: List[Booking] = []

    # read-only access to currently loaded in-memory bookings
    @property
    def confirmed_bookings(self) -> List[Booking]:
        return self._confirmed_bookings.copy()

    def create_booking(
            self,
            offer: Offer,
            traveler: TravelerProfile,
            num_seats: Optional[int] = None,
    ) -> Booking:
        seats_to_book = num_seats or traveler.required_seats

        if seats_to_book <= 0:
            raise InvalidRecordError("Must reserve at least 1 seat.")

        if offer.available_seats < seats_to_book:
            raise InvalidRecordError(
                f"Booking failed: Offer '{offer.offer_id}' has {offer.available_seats} available seats, but "
                f"{seats_to_book} were requested."
            )

        # 1. decrement seat capacity
        offer.decrement_seats(seats_to_book)

        # 2. generate unique booking reference
        booking_ref = BookingReferenceGenerator.generate(offer.origin)

        # 3. create domain booking instance
        booking = Booking(
            booking_reference=booking_ref,
            offer=offer,
            traveler=traveler,
            num_seats=seats_to_book,
            booking_timestamp=datetime.now(),
            status="CONFIRMED"
        )

        # 4. store in memory and append to persistent files
        self._confirmed_bookings.append(booking)
        self._append_booking_to_csv(booking)
        self._append_receipt_to_txt(booking)

        return booking

    def _append_booking_to_csv(self, booking: Booking) -> None:
        file_exists = self.bookings_csv_path.exists()

        with open(self.bookings_csv_path, "a", newline="") as f:
            writer = csv.writer(f)

            # write header if file is freshly created
            if not file_exists or self.bookings_csv_path.stat().st_size == 0:
                writer.writerow([
                    "booking_reference",
                    "offer_id",
                    "company_id",
                    "company_name",
                    "traveler_name",
                    "origin",
                    "destination",
                    "traveler_date",
                    "departure_time",
                    "num_seats",
                    "total_price_eur",
                    "status",
                    "booking_timestamp",
                ])
            writer.writerow([
                booking.booking_reference,
                booking.offer.offer_id,
                booking.offer.company.company_id,
                booking.offer.company.name,
                booking.traveler.name,
                booking.offer.origin,
                booking.offer.destination,
                booking.offer.travel_date.strftime("%Y-%m-%d"),
                booking.offer.departure_time.strftime("%H:%M"),
                booking.num_seats,
                f"{booking.total_price:.2f}",
                booking.status,
                booking.booking_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ])

    def _append_receipt_to_txt(self, booking: Booking) -> None:
        with open(self.receipts_txt_path, mode="a", encoding="utf-8") as f:
            f.write(booking.summary() + "\n\n")