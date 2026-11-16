import unittest
import tempfile
from pathlib import Path
from datetime import date, time

from pip._internal.utils import temp_dir

from exceptions import InvalidRecordError, InvalidIdentifierError
from models import Company, FareCondition, Offer, TravelerProfile, Booking
from validators import validate_booking_reference, validate_company_id, validate_offer_id
from filters import DestinationFilter, BudgetFilter, FilterPipeline
from scoring import ScoringEngine, MinMaxNormalizer
from loader import load_companies, load_offers, RejectedRecord
from booking import  BookingManager, BookingReferenceGenerator

class TestDomainModels(unittest.TestCase):
    def setUp(self):
        self.company = Company("COMP-SOL01", "SolRuta", "low_cost", fleet_rating=4.2)
        self.fare = FareCondition(is_changeable=True, is_refundable=False)
        self.offer = Offer(
            offer_id = "OFF-MAD-BCN-101",
            company = self.company,
            origin="Madrid",
            destination="Barcelona",
            travel_date = date(2026, 7, 12),
            departure_time = time(8, 0),
            arrival_time = time(14, 0),
            duration_minutes = 360,
            price=30.0,
            transfers=0,
            available_seats = 5,
            customer_rating = 4.5,
            co2_emissions_kg = 15.0,
            fare_condition = self.fare
        )

    def test_company_invalid_rating(self):
        with self.assertRaises(ValueError):
            Company("COMP-BAD01", "Bad Bus", "low_cost", fleet_rating=6.0)

    def test_offer_seat_decrement_success(self):
        self.assertEqual(self.offer.available_seats, 5)
        self.offer.decrement_seats(2)
        self.assertEqual(self.offer.available_seats, 3)

    def test_offer_decrement_exceeding_capacity(self):
        with self.assertRaises(ValueError):
            self.offer.decrement_seats(10)



class TestValidators(unittest.TestCase):
    def test_valid_booking_reference(self):
        self.assertTrue(validate_booking_reference("BB-MAD-123456"))
        self.assertTrue(validate_booking_reference("BB-BCN-000001"))

    def test_invalid_booking_reference(self):
        invalid_refs = ["BB-MAD-123", "BB-mad-123456", "INVALID_REF", "BB-MAD-1234567"]
        for ref in invalid_refs:
            with self.subTest(ref=ref):
                with self.assertRaises(InvalidIdentifierError):
                    validate_booking_reference(ref)

    def test_valid_company_id(self):
        self.assertTrue(validate_company_id("COMP-SOL01"))

    def test_invalid_company_id(self):
        with self.assertRaises(InvalidIdentifierError):
            validate_company_id("SOLRUTA-01")

class TestFilters(unittest.TestCase):
    def setUp(self):
        self.company = Company("COMP-SOL01", "SolRuta", "express")
        self.fare = FareCondition(is_changeable=False, is_refundable=False)
        self.offer = Offer(
            "OFF-MAD-BCN-101", self.company, "Madrid", "Barcelona",
            date(2026, 7, 12), time(8, 0), time(14, 0), 360,
            price=50.0, transfers=0, available_seats=5, customer_rating=4.0,
            co2_emissions_kg = 15.0, fare_condition = self.fare
        )

    def test_budget_filter_disqualifies_over_budget(self):
        profile = TravelerProfile(
            "Ana", "Madrid", "Barcelona", date(2026, 7, 10), date(2026, 7, 15), max_budget=40.0
        )
        budget_filter = BudgetFilter()
        satisfied, reason = budget_filter.evaluate(self.offer, profile)
        self.assertFalse(satisfied)
        self.assertIn("exceeds maximum budget", reason)

    def test_filter_pipeline_disqualifies_over_budget(self):
        profile = TravelerProfile(
            "Ana",
            "Madrid",
            "Barcelona",
            date(2026, 7, 10),
            date(2026, 7, 15),
            max_budget=40.0
        )
        budget_filter = BudgetFilter()
        satisfied, reason = budget_filter.evaluate(self.offer, profile)
        self.assertFalse(satisfied)
        self.assertIn("exceeds maximum budget", reason)

    def test_filter_pipeline_disqualifies_invalid_destination(self):
        profile = TravelerProfile(
            "Ana", "Madrid", "Valencia", date(2026, 7, 10), date(2026, 7, 15)
        )
        pipeline = FilterPipeline()
        eligible, disqualified = pipeline.filter_offers([self.offer], profile)
        self.assertEqual(len(eligible), 0)
        self.assertEqual(len(disqualified), 1)
        self.assertIn("Destination mismatch", disqualified[0][2])

class TestScoringEngine(unittest.TestCase):
    def test_min_max_normalization_lower_is_better(self):
        score_min = MinMaxNormalizer.normalize_lower_is_better(20.0, 20.0, 50.0)
        score_max = MinMaxNormalizer.normalize_lower_is_better(50.0, 20.0, 50.0)
        score_mid = MinMaxNormalizer.normalize_lower_is_better(35.0, 20.0, 50.0)

        self.assertEqual(score_min, 100.0)
        self.assertEqual(score_max, 0.0)
        self.assertEqual(score_mid, 50.0)

    def test_normalization_uniform_values_neutral_fallback(self):
        score = MinMaxNormalizer.normalize_lower_is_better(30.0, 30.0, 30.0)
        self.assertEqual(score, 100.0)

class TestLoaderAndRejectedRecords(unittest.TestCase):
    def test_corrupt_offer_row(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            companies_csv = Path(tmpdir) / "companies.csv"
            offers_csv = Path(tmpdir) / "offers.csv"

            companies_csv.write_text(
                "company_id,name,profile_type,fleet_rating,eco_certified\n"
                "COMP-SOL01,SolRuta,low_cost,4.0,false\n"
            )

            offers_csv.write_text(
                "offer_id,company_id,origin,destination,travel_date,departure_time,arrival_time,"
                "duration_minutes,price,transfers,available_seats,customer_rating,co2_emissions_kg,"
                "is_changeable,is_refundable,luggage_kg,change_fee_eur\n"
                "OFF-MAD-BCN-101,COMP-SOL01,Madrid,Barcelona,2026-07-12,08:00:00,14:00:00,360,"
                "invalid_price,0,10,4.0,15.0,false,false,20.0,0.0\n"
            )

            rejected_records = []
            companies = load_companies(companies_csv, rejected_records)
            offers = load_offers(offers_csv, companies, rejected_records)

            self.assertEqual(len(offers), 0)
            self.assertEqual(len(rejected_records), 1)
            self.assertIn("offers.csv", rejected_records[0].filename)

class TestBookingManager(unittest.TestCase):
    def test_create_booking(self):
        company = Company("COMP-SOL01", "SolRuta", "Express")
        fare = FareCondition(is_changeable=True, is_refundable=True)
        offer = Offer(
            "OFF-MAD-BCN-101", company, "Madrid", "Barcelona",
            date(2026, 7, 12), time(8, 0), time(14, 0), 360,
            price=35.0, transfers=0, available_seats=4, customer_rating=4.5,
            co2_emissions_kg=15.0, fare_condition=fare
        )

        profile = TravelerProfile(
            "Bookingtest", "Madrid", "Barcelona", date(2026, 7, 10), date(2026, 7, 15), required_seats=2
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = BookingManager(output_dir=Path(tmp_dir))
            booking = mgr.create_booking(offer, profile)

            self.assertEqual(offer.available_seats, 2)
            self.assertTrue(validate_booking_reference(booking.booking_reference))
            self.assertTrue((Path(tmp_dir) / "bookings.csv").exists())

if __name__ == "__main__":
    unittest.main()