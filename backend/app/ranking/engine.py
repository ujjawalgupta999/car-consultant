from typing import List, Dict, Any, Optional
from ..models.vehicle import Vehicle
from ..models.preferences import UserPreferences, IntentType
from ..marketplace.availability import is_vehicle_available_for_dates

class RecommendationItem:
    def __init__(
        self,
        vehicle: Vehicle,
        match_score: float,
        score_breakdown: Dict[str, float],
        estimated_total_cost: float,
        currency: str,
        positive_matches: List[str],
        trade_offs: List[str],
        explanation: str,
        availability_status: str = "AVAILABLE"
    ):
        self.vehicle = vehicle
        self.match_score = round(match_score, 1)
        self.score_breakdown = score_breakdown
        self.estimated_total_cost = estimated_total_cost
        self.currency = currency
        self.positive_matches = positive_matches
        self.trade_offs = trade_offs
        self.explanation = explanation
        self.availability_status = availability_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vehicle": self.vehicle.model_dump(),
            "match_score": self.match_score,
            "score_breakdown": self.score_breakdown,
            "estimated_total_cost": self.estimated_total_cost,
            "currency": self.currency,
            "positive_matches": self.positive_matches,
            "trade_offs": self.trade_offs,
            "explanation": self.explanation,
            "availability_status": self.availability_status
        }

class RankingEngine:
    @staticmethod
    def rank_vehicles(
        vehicles: List[Vehicle],
        preferences: UserPreferences,
        limit: int = 5
    ) -> List[RecommendationItem]:
        is_rent = (preferences.intent == IntentType.RENT)
        user_budget_amount = preferences.budget.amount if preferences.budget else None
        
        # Determine rental duration for total cost
        duration_days = 1
        if is_rent and preferences.rental_details and preferences.rental_details.rental_duration_days:
            duration_days = preferences.rental_details.rental_duration_days
        elif not is_rent and preferences.purchase_details and preferences.purchase_details.purchase_budget:
            user_budget_amount = preferences.purchase_details.purchase_budget

        has_brand_pref = bool(preferences.preferred_brands)

        # Dynamic weights redistribution:
        # If no brand preference specified, brand_weight (10) is redistributed:
        # Budget: 33%, Category: 28%, Preferences: 22%, Rating: 17% (Total: 100%)
        if has_brand_pref:
            w_budget = 30.0
            w_category = 25.0
            w_pref = 20.0
            w_rating = 15.0
            w_brand = 10.0
        else:
            w_budget = 33.3
            w_category = 27.8
            w_pref = 22.2
            w_rating = 16.7
            w_brand = 0.0

        recommendations: List[RecommendationItem] = []

        for v in vehicles:
            # 1. Budget Score
            if is_rent:
                price = v.rental_price_per_day
            else:
                price = v.purchase_price

            if user_budget_amount and user_budget_amount > 0:
                if price <= user_budget_amount:
                    # Within budget: ratio between 75% and 100% based on efficiency
                    ratio = price / user_budget_amount
                    # Vehicles closer to budget or delivering optimal value get highest score
                    budget_score = w_budget * (0.85 + 0.15 * (1.0 - abs(0.9 - ratio)))
                else:
                    over_ratio = (price - user_budget_amount) / user_budget_amount
                    budget_score = max(0.0, w_budget * (1.0 - over_ratio * 2))
            else:
                budget_score = w_budget * 0.9

            # 2. Category Score
            if preferences.category:
                if v.category == preferences.category:
                    cat_score = w_category
                else:
                    cat_score = 0.0
            else:
                cat_score = w_category * 0.9

            # 3. Preference Compatibility Score (Fuel, Transmission, Seats)
            pref_points = 0.0
            max_pref_points = 3.0

            # Transmission
            if preferences.transmission and preferences.transmission.lower() not in ["any", ""]:
                if v.transmission.value.lower() == preferences.transmission.lower():
                    pref_points += 1.0
            else:
                pref_points += 1.0

            # Fuel type
            if preferences.fuel_type and preferences.fuel_type.lower() not in ["any", ""]:
                if v.fuel_type.value.lower() == preferences.fuel_type.lower():
                    pref_points += 1.0
            else:
                pref_points += 1.0

            # Seats
            if preferences.seating_capacity:
                if v.seats >= preferences.seating_capacity:
                    pref_points += 1.0
            else:
                pref_points += 1.0

            pref_score = w_pref * (pref_points / max_pref_points)

            # 4. Rating Score (Rating from 3.0 to 5.0 normalized)
            norm_rating = max(0.0, min(1.0, (v.rating - 3.0) / 2.0))
            rating_score = w_rating * norm_rating

            # 5. Brand Preference Score
            if has_brand_pref:
                if any(v.brand.lower() == b.lower() for b in preferences.preferred_brands):
                    brand_score = w_brand
                else:
                    brand_score = 0.0
            else:
                brand_score = 0.0

            total_score = min(100.0, max(0.0, budget_score + cat_score + pref_score + rating_score + brand_score))

            # Calculated total cost
            if is_rent:
                total_cost = v.rental_price_per_day * duration_days
            else:
                total_cost = v.purchase_price

            # Positive Matches
            positives: List[str] = []
            if v.category == preferences.category:
                positives.append(f"Matches requested category ({v.category.value})")
            if user_budget_amount and price <= user_budget_amount:
                if is_rent:
                    savings = user_budget_amount - price
                    positives.append(f"₹{price:,.0f}/day is under your budget ceiling of ₹{user_budget_amount:,.0f} (Save ₹{savings:,.0f}/day)")
                else:
                    positives.append(f"₹{price:,.0f} purchase price satisfies your ₹{user_budget_amount:,.0f} budget")
            if preferences.transmission and preferences.transmission.lower() == v.transmission.value.lower():
                positives.append(f"{v.transmission.value.capitalize()} transmission as specified")
            if preferences.fuel_type and preferences.fuel_type.lower() == v.fuel_type.value.lower():
                positives.append(f"{v.fuel_type.value.capitalize()} powertrain as requested")
            if has_brand_pref and any(v.brand.lower() == b.lower() for b in preferences.preferred_brands):
                positives.append(f"Preferred brand ({v.brand}) match")
            if v.rating >= 4.7:
                positives.append(f"High customer rating ({v.rating}★ from {v.review_count} verified reviews)")

            # Trade-offs / Compromises
            trade_offs: List[str] = []
            if v.condition.value == "used":
                trade_offs.append(f"Pre-owned vehicle ({v.odometer_km:,.0f} km on odometer)")
            if is_rent and price > (user_budget_amount or 0):
                trade_offs.append(f"Exceeds daily budget by ₹{(price - user_budget_amount):,.0f}/day")
            if v.fuel_type.value == "petrol" and not preferences.fuel_type:
                trade_offs.append("Petrol fuel economy (~16-17 kmpl) compared to hybrid/EV alternatives")

            # Truthful, data-driven explanation
            if is_rent:
                expl = (
                    f"The {v.year} {v.brand} {v.model} is an excellent match for your {preferences.location or 'city'} rental. "
                    f"At ₹{v.rental_price_per_day:,.0f}/day (₹{total_cost:,.0f} for {duration_days} days), it features {v.transmission.value} transmission "
                    f"and {v.seats} seats. Key features include {', '.join(v.features[:3])}."
                )
            else:
                expl = (
                    f"The {v.year} {v.brand} {v.model} is a high-value purchase candidate in {v.location}. "
                    f"Offered at ₹{v.purchase_price:,.0f} in {v.condition.value} condition ({v.odometer_km:,.0f} km). "
                    f"It delivers {v.rating}★ reliability with features such as {', '.join(v.features[:3])}."
                )

            score_breakdown = {
                "budget_score": round(budget_score, 1),
                "category_score": round(cat_score, 1),
                "preference_score": round(pref_score, 1),
                "rating_score": round(rating_score, 1),
                "brand_score": round(brand_score, 1)
            }

            rec = RecommendationItem(
                vehicle=v,
                match_score=total_score,
                score_breakdown=score_breakdown,
                estimated_total_cost=total_cost,
                currency="INR",
                positive_matches=positives,
                trade_offs=trade_offs,
                explanation=expl,
                availability_status="AVAILABLE"
            )
            recommendations.append(rec)

        # Sort descending by match score
        recommendations.sort(key=lambda r: r.match_score, reverse=True)
        return recommendations[:limit]

    @staticmethod
    def diagnose_zero_results(
        all_vehicles: List[Vehicle],
        preferences: UserPreferences
    ) -> Dict[str, Any]:
        """
        Determines which constraints eliminated inventory and recommends relaxations.
        """
        reasons = []
        suggestions = []
        is_rent = (preferences.intent == IntentType.RENT)

        # 1. Category check
        if preferences.category:
            matching_cat = [v for v in all_vehicles if v.category == preferences.category]
            if not matching_cat:
                reasons.append(f"No listings found in category '{preferences.category.value}'.")
                suggestions.append("Consider exploring an adjacent category like SUV or Sedan.")
            else:
                # 2. Budget check within category
                budget_ceiling = preferences.budget.amount if preferences.budget else 0
                if is_rent and budget_ceiling > 0:
                    min_price = min(v.rental_price_per_day for v in matching_cat)
                    if budget_ceiling < min_price:
                        reasons.append(
                            f"Your daily budget ceiling of ₹{budget_ceiling:,.0f} is below the lowest {preferences.category.value} rate (₹{min_price:,.0f}/day)."
                        )
                        suggestions.append(f"Increase your daily budget to at least ₹{min_price:,.0f}/day, or consider a Hatchback or Sedan.")
                elif not is_rent and budget_ceiling > 0:
                    min_price = min(v.purchase_price for v in matching_cat)
                    if budget_ceiling < min_price:
                        reasons.append(
                            f"Your purchase budget of ₹{budget_ceiling:,.0f} is below the entry price for {preferences.category.value} (₹{min_price:,.0f})."
                        )
                        suggestions.append(f"Increase purchase budget to at least ₹{min_price:,.0f} or select a pre-owned Hatchback or Sedan.")

        # 3. Transmission check
        if preferences.transmission and preferences.transmission.lower() not in ["any", ""]:
            matching_trans = [v for v in all_vehicles if v.transmission.value.lower() == preferences.transmission.lower()]
            if not matching_trans:
                reasons.append(f"No vehicles found with {preferences.transmission} transmission.")
                suggestions.append("Consider selecting 'any' transmission.")

        if not reasons:
            reasons.append("No vehicles currently meet your combined location, date, and budget filters.")
            suggestions.append("Try relaxing your budget or adjusting your travel dates.")

        return {
            "binding_constraints": reasons,
            "recommended_relaxations": suggestions
        }

