from decimal import Decimal
from typing import Any, Dict


def convert_decimals(obj: Any) -> Any:
    """Recursively converts Decimal values to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


def calculate_budget_and_installments(total_budget: float) -> Dict[str, Any]:
    """
    Calculates a wedding budget breakdown into standard categories and generates
    3-month and 6-month BNPL (Buy-Now-Pay-Later) installment plans (similar to Koko/Mintpay).

    Parameters:
        total_budget (float): The couple's total wedding budget in Sri Lankan Rupees (LKR).

    Returns:
        Dict[str, Any]: JSON-serializable dictionary with budget category splits and BNPL plans.
    """
    # Safeguard against negative or zero budgets
    budget = float(total_budget) if total_budget > 0 else 1000000.0

    # 1. Budget breakdown percentages
    # Hotel (40%), Catering (30%), Photography (15%), Decorations (10%), Music (5%)
    hotel_amount = round(budget * 0.40, 2)
    catering_amount = round(budget * 0.30, 2)
    photography_amount = round(budget * 0.15, 2)
    decorations_amount = round(budget * 0.10, 2)
    music_amount = round(budget * 0.05, 2)

    # 2. Buy-Now-Pay-Later (BNPL) calculations (Koko / Mintpay style)
    # 3-Month Plan (3 equal monthly installments)
    three_month_installment = round(budget / 3.0, 2)
    # 6-Month Plan (6 equal monthly installments)
    six_month_installment = round(budget / 6.0, 2)

    result = {
        "status": "success",
        "total_budget_lkr": float(budget),
        "currency": "LKR",
        "category_breakdown": {
            "hotel_and_venue": {
                "percentage": 40,
                "allocated_amount_lkr": float(hotel_amount),
                "description": "Ballroom / hall rental, venue fees, and guest accommodations."
            },
            "catering_and_banquet": {
                "percentage": 30,
                "allocated_amount_lkr": float(catering_amount),
                "description": "Food, welcome drinks, desserts, and service staff."
            },
            "photography_and_video": {
                "percentage": 15,
                "allocated_amount_lkr": float(photography_amount),
                "description": "Pre-shoot, main day photo & video coverage, drone, and wedding albums."
            },
            "decorations_and_floral": {
                "percentage": 10,
                "allocated_amount_lkr": float(decorations_amount),
                "description": "Poruwa/altar decor, entrance arch, table centerpieces, and lighting."
            },
            "music_and_entertainment": {
                "percentage": 5,
                "allocated_amount_lkr": float(music_amount),
                "description": "Live wedding band, sound engineering, and DJ setup."
            }
        },
        "bnpl_installment_plans": {
            "platform_partner": "Koko / Mintpay BNPL",
            "three_month_plan": {
                "total_installments": 3,
                "monthly_payment_lkr": float(three_month_installment),
                "initial_downpayment_lkr": float(three_month_installment),
                "interest_rate": "0% interest",
                "payment_schedule": "1st installment due on booking, 2nd installment in 30 days, 3rd in 60 days."
            },
            "six_month_plan": {
                "total_installments": 6,
                "monthly_payment_lkr": float(six_month_installment),
                "initial_downpayment_lkr": float(six_month_installment),
                "interest_rate": "0% interest",
                "payment_schedule": "Spread over 6 equal monthly payments leading up to the wedding."
            }
        }
    }

    return convert_decimals(result)
