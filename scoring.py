"""
Min-Max feature scaling across heterogeneous
criteria and computes weighted recommendation scores
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from models import Offer, TravelerProfile

@dataclass
class ScoredOffer:
    offer: Offer
    total_score: float
    criterion_scores: Dict[str, float]
    raw_metrics: Dict[str, float]

    def __repr__(self) -> str:
        return (
            f"ScoredOffer({self.offer.offer_id}, Carrier={self.offer.company.name}, "
            f"Score={self.total_score:.2f}/100, Price=EUR {self.offer.price:.2f})"
        )

"""
normalizes heterogeneous metric values to a standardized 0.0-100.0 range
handles both "lower-is-better" and "higher-is-better"
"""
class MinMaxNormalizer:
    @staticmethod
    def normalize_lower_is_better(value: float, min_val: float, max_val: float) -> float:
        if max_val == min_val:
            return 100.0
        score = 100.0 * (max_val - value) / (max_val - min_val)
        return max(0.0, min(100.0, score))

    @staticmethod
    def normalize_higher_is_better(value: float, min_val: float, max_val: float) -> float:
        if max_val == min_val:
            return 100.0
        score = 100.0 * (value - min_val) / (max_val - min_val)
        return max(0.0, min(100.0, score))

class ScoringEngine:
    """
    direction metadata for all supported criteria
    True = higher is better
    False = lower is better
    """
    CRITERIA_DIRECTIONS = {
        "price": False,
        "duration": False,
        "departure_convenience": False,
        "flexibility": True,
        "rating": True,
        "emissions": True,
    }

    def __init__(self):
        self.normalizer = MinMaxNormalizer()

    @staticmethod
    def extract_raw_metrics(offer: Offer, profile: TravelerProfile) -> Dict[str, float]:
        pref_mins = profile.preferred_departure_time.hour * 60 + profile.preferred_departure_time.minute
        actual_mins = offer.departure_minutes_from_midnight()
        departure_diff_mins = float(abs(actual_mins - pref_mins))

        return {
            "price": float(offer.price),
            "duration": float(offer.duration_minutes),
            "departure_convenience": departure_diff_mins,
            "flexibility": float(offer.fare_condition.flexibility_score()), # higher = better
            "rating": float(offer.customer_rating), # higher = better
            "emissions": float(offer.co2_emissions_kg), #lower = better
        }

    def score_offers(
            self,
            eligible_offers: List[Offer],
            profile: TravelerProfile
    ) -> List[ScoredOffer]:

        if not eligible_offers:
            return []

        weights = profile.weights

        # 1. extract raw metric vectors for all candidate offers
        offer_raw_data: List[Tuple[Offer, Dict[str, float]]] = [
            (offer, self.extract_raw_metrics(offer, profile)) for offer in eligible_offers
        ]

        # 2. determine Min and Max bounds across the candidate pool for each metric
        all_criteria = list(self.CRITERIA_DIRECTIONS.keys())
        bounds: Dict[str, Tuple[float, float]] = {}

        for key in all_criteria:
            vals = [raw[key] for _, raw in offer_raw_data]
            bounds[key] = (min(vals), max(vals))

        # 3. normalize individual metrics and compute weighted scores
        scored_results: List[ScoredOffer] = []

        for offer, raw in offer_raw_data:
            criterion_scores: Dict[str, float] = {}

            for criterion, higher_is_better in self.CRITERIA_DIRECTIONS.items():
                min_val, max_val = bounds[criterion]
                val = raw[criterion]

                if higher_is_better:
                    score = self.normalizer.normalize_higher_is_better(val, min_val, max_val)
                else:
                    score = self.normalizer.normalize_lower_is_better(val, min_val, max_val)

                criterion_scores[criterion] = score

            # 4. calculate total weighted score using weights present in profile
            total_score = 0.0
            active_weight_sum = 0.0

            for criterion, weight in weights.items():
                if criterion in criterion_scores:
                    total_score += weight * criterion_scores[criterion]
                    active_weight_sum += weight

            # re-scale if profile weights do not include all 6 criteria
            if active_weight_sum > 0:
                total_score = total_score / active_weight_sum

            scored_offer = ScoredOffer(
                offer=offer,
                total_score=round(total_score, 2),
                criterion_scores={k: round(v, 2) for k, v in criterion_scores.items()},
                raw_metrics=raw
            )
            scored_results.append(scored_offer)

        # 5. sort offers in descending order by total score
        scored_results.sort(key=lambda x: x.total_score, reverse=True)
        return scored_results
