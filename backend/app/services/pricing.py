from typing import List, Dict
from ..models.vehicle import Vehicle
from ..models.booking import AddOn, PriceBreakdown

ADDON_CATALOG: Dict[str, AddOn] = {
    "addon_insurance_zero_dep": AddOn(
        id="addon_insurance_zero_dep",
        name="Zero Depreciation Protection",
        price_per_day=300.0,
        description="Covers 100% of body and mechanical repair costs with zero deductible."
    ),
    "addon_roadside_assist": AddOn(
        id="addon_roadside_assist",
        name="24/7 Premium Roadside Assistance",
        price_per_day=150.0,
        description="Emergency towing, flat tyre support, and battery jumpstart anywhere in India."
    ),
    "addon_child_seat": AddOn(
        id="addon_child_seat",
        name="ISOFIX Child Safety Seat",
        price_per_day=100.0,
        description="Approved rear/forward facing safety seat for infants and toddlers."
    ),
    "addon_extra_driver": AddOn(
        id="addon_extra_driver",
        name="Additional Authorized Driver",
        price_per_day=200.0,
        description="Includes insurance coverage for a secondary registered driver."
    )
}

TAX_RATE_GST = 0.18 # 18% standard GST on vehicle rentals

def calculate_rental_total(
    vehicle: Vehicle,
    duration_days: int,
    addon_ids: List[str]
) -> PriceBreakdown:
    if duration_days < 1:
        duration_days = 1

    base_rate = vehicle.rental_price_per_day
    subtotal = base_rate * duration_days

    addons_total = 0.0
    for aid in addon_ids:
        if aid in ADDON_CATALOG:
            addons_total += ADDON_CATALOG[aid].price_per_day * duration_days

    taxable_amount = subtotal + addons_total
    taxes = round(taxable_amount * TAX_RATE_GST, 2)
    total_amount = round(taxable_amount + taxes, 2)

    return PriceBreakdown(
        base_rate=base_rate,
        duration_days=duration_days,
        subtotal=subtotal,
        addons_total=addons_total,
        taxes=taxes,
        total_amount=total_amount,
        currency="INR"
    )

def calculate_purchase_summary(
    vehicle: Vehicle,
    deposit_amount: float = 25000.0
) -> Dict[str, float]:
    purchase_price = vehicle.purchase_price
    rto_registration = round(purchase_price * 0.10, 2) # approx 10% road tax/RTO
    tcs = round(purchase_price * 0.01, 2) # 1% TCS
    on_road_estimated = purchase_price + rto_registration + tcs

    return {
        "ex_showroom_price": purchase_price,
        "rto_registration": rto_registration,
        "tcs_tax": tcs,
        "on_road_estimated": on_road_estimated,
        "token_deposit": deposit_amount,
        "balance_payable": on_road_estimated - deposit_amount
    }

