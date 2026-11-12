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

    @staticmethod
    def comfort_tourist(
            name: str = "Sofia (Comfort)",
            origin: str = "Madrid",
            destination: str = "Barcelona",
            start_date: date = date(2026, 7, 12),
            end_date: date = date(2026, 7, 15)
    ) -> TravelerProfile:
        return TravelerProfile(
            name=name,
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            requires_refundable=True,
            weights={
                "flexibility": 0.40,
                "rating": 0.30,
                "price": 0.20,
                "duration": 0.10,
            }
        )

    @staticmethod
    def eco_traveler(
            name: str = "Diego (Eco)",
            origin: str = "Madrid",
            destination: str = "Barcelona",
            start_date: date = date(2026, 7, 12),
            end_date: date = date(2026, 7, 15)
    ) -> TravelerProfile:
        return TravelerProfile(
            name=name,
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            weights={
                "emissions": 0.40,
                "price": 0.30,
                "duration": 0.20,
                "departure_convenience": 0.10,
            }
        )

"""
analyzes scored offers and makes an explainable report.
synthesizes pros, cons, trade-offs, and profile-relative decision rationales
"""
class RecommendationExplainer:
    def analyze_offers(
            self,
            scored: ScoredOffer,
    ) -> Dict[str, List[str]]:
        offer = scored.offer
        sub_scores = scored.criterion_scores
        raw = scored.raw_metrics

        pros = []
        cons = []

        # price analysis
        if sub_scores.get("price", 0) >= 75.0:
            pros.append(f"Highly competitive fare (EUR {offer.price:.2f})")
        elif sub_scores.get("price", 0) <= 35.0:
            cons.append(f"Higher price point (EUR {offer.price:.2f})")

        # duration and transfers
        if offer.transfers == 0:
            pros.append("Direct non-stop journey.")
        else:
            cons.append(f"Includes {offer.transfers} transfer(s).")

        if sub_scores.get("duration", 0) >= 75.0:
            pros.append(f"Fast travel time ({offer.duration_minutes} minutes).")
        elif sub_scores.get("duration", 0) <= 35.0:
            cons.append(f"Slower journey duration ({offer.duration_minutes} minutes).")

        # flexibility
        fare = offer.fare_condition
        if fare.is_changeable and fare.is_refundable:
            pros.append("Fully flexible ticket (changeable and refundable).")
        elif fare.is_changeable:
            pros.append(f"Ticket changeable (Fee: EUR {fare.change_fee_eur:.2f}).")
        else:
            cons.append("Strict non-changeable and non-refundable fare.")

        # eco and carrier
        if offer.company.eco_certified:
            pros.append(f"Operated by eco-certified carrier ({offer.company.name}).")
        if sub_scores.get("emissions", 0) >= 75.0:
            pros.append(f"Low carbon footprint ({offer.co2_emissions_kg:.1f} kg CO2).")

        # rating
        if offer.customer_rating >= 4.5:
            pros.append(f"High customer rating ({offer.customer_rating:.1f}/5.0 stars).")

        return {"pros": pros, "cons": cons}

    def generate_recommendation_rationale(
            self,
            top_pick: ScoredOffer,
            runner_up: Optional[ScoredOffer],
            profile: TravelerProfile
    ) -> str:
        weights = profile.weights
        top_driver = max(weights.items(), key=lambda x: x[1])[0]
        driver_score = top_pick.criterion_scores.get(top_driver, 0.0)

        rationale = (
            f"'{top_pick.offer.offer_id}' operated by {top_pick.offer.company.name} "
            f"is recommended as the top match for {profile.name} with a total composite score of"
            f"{top_pick.total_score:.1f}/100. "
            f"The primary preference driver for this profile was '{top_driver}' (weight {weights[top_driver]*100:.0f}%), "
            f"where this offer scored {driver_score:.1f}/100. "
        )

        if runner_up:
            margin = top_pick.total_score - runner_up.total_score
            rationale += (
                f"It outranked runner-up '{runner_up.offer.offer_id}' ({runner_up.offer.company.name} "
                f"by a margin of {margin:.1f} points."
            )
            # key difference
            if top_pick.offer.price < runner_up.offer.price:
                diff = runner_up.offer.price - top_pick.offer.price
                rationale += f"Key advantage: EUR {diff:.2f} cheaper than the runner-up."
            elif top_pick.offer.duration_minutes < runner_up.offer.duration_minutes:
                diff = runner_up.offer.duration_minutes - top_pick.offer.duration_minutes
                rationale += f"Key advantage: {diff} minutes faster than the runner-up."

        return rationale

    def format_full_recommendation_report(
            self,
            scored_offers: List[ScoredOffer],
            profile: TravelerProfile
    ) -> str:
        if not scored_offers:
            return (
                f"==================================================\n"
                f"      BUSBIDDER SPAIN - RECOMMENDATION REPORT     \n"
                f"==================================================\n"
                f"Traveler Profile  : {profile.name}\n"
                f"Route             : {profile.origin} -> {profile.destination}\n"
                f"--------------------------------------------------\n"
                f"No eligible offers matched the requested requirements.\n"
                f"===================================================\n"
            )
        top_pick = scored_offers[0]
        runner_up = scored_offers[1] if len(scored_offers) > 1 else None
        analysis = self.analyze_offers(top_pick)
        rationale = self.generate_recommendation_rationale(top_pick, runner_up, profile)

        report = []
        report.append("=================================================")
        report.append("     BUSBIDDER SPAIN - RECOMMENDATION REPORT     ")
        report.append("=================================================")
        report.append(f"Traveler Profile  : {profile.name}")
        report.append(f"Route             : {profile.origin} -> {profile.destination}")
        report.append(f"Travel Window     : {profile.start_date} to {profile.end_date}")
        report.append("-------------------------------------------------")
        report.append(f"RECOMMENDED OFFER  : {top_pick.offer.offer_id}")
        report.append(f"Carrier            : {top_pick.offer.company.name} ({top_pick.offer.company.profile_type})")
        report.append(f"Composite Score    : {top_pick.total_score:.1f}/100.0")
        report.append(f"Fare Price         : EUR {top_pick.offer.price:.2f}")
        report.append(f"Departure & Arrival: {top_pick.offer.departure_time.strftime('%H:%M')} -> {top_pick.offer.arrival_time.strftime('%H:%M')} ({top_pick.offer.duration_minutes} mins")
        report.append("-------------------------------------------------")
        report.append("DECISION RATIONALE:")
        report.append(f"    {rationale}")
        report.append("-------------------------------------------------")
        report.append("KEY ADVANTAGE(S) (PROS):")
        for pro in analysis["pros"]:
            report.append(f"   [+]  {pro}")
        if not analysis["pros"]:
            report.append("   [+]  Meets basic requirements.")

        report.append("KEY TRADE-OFFS (CONS):")
        for con in analysis["cons"]:
            report.append(f"   [-]  {con}")
        if not analysis["cons"]:
            report.append("   [-]  No significant trade-offs found.")

        report.append("-----------------------------------------------")
        report.append("SUMMARY:")
        for rank, item in enumerate(scored_offers[:5], start=1):
            report.append(
                f"  Rank {rank}: {item.offer.offer_id} | {item.offer.company.name} | "
                f"EUR {item.offer.price:.2f} | {item.offer.duration_minutes}m | "
                f"Score: {item.total_score:.1f}"
            )
        report.append("===================================================\n")

        return "\n".join(report)