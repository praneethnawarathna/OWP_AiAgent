from decimal import Decimal
from typing import Any, Dict, List


def convert_decimals(obj: Any) -> Any:
    """Recursively converts Decimal values to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


def plan_catering_menu(
    budget_per_plate: float,
    is_vegetarian: bool = False,
    time_of_day: str = "dinner"
) -> Dict[str, Any]:
    """
    Builds a customized wedding catering menu based on price per plate,
    dietary preference (vegetarian vs non-vegetarian), and event timing (lunch vs dinner).

    Parameters:
        budget_per_plate (float): Target price per plate/head in Sri Lankan Rupees (LKR).
        is_vegetarian (bool): True if pure vegetarian/vegan, False for standard omnivore/halal.
        time_of_day (str): 'lunch' (afternoon) or 'dinner' (evening/night).

    Returns:
        Dict[str, Any]: JSON-serializable dictionary with structured menu courses, items, and service advice.
    """
    plate_budget = float(budget_per_plate) if budget_per_plate > 0 else 4500.0
    time_clean = (time_of_day or "dinner").strip().lower()
    is_lunch = "lunch" in time_clean or "afternoon" in time_clean
    meal_slot = "Lunch Reception" if is_lunch else "Dinner Banquet"

    # Determine tier based on budget
    if plate_budget < 3500.0:
        tier_name = "Silver Essential"
    elif plate_budget < 6000.0:
        tier_name = "Gold Premium"
    else:
        tier_name = "Platinum Imperial Royal"

    # 1. Welcome Drinks
    if is_lunch:
        welcome_drinks = [
            "Chilled King Coconut with Fresh Lime & Mint",
            "Passion Fruit & Wild Berry Spritzer",
            "Ceylon Spiced Iced Tea"
        ]
    else:
        welcome_drinks = [
            "Sparkling Guava & Rosemary Fizz",
            "Virgin Mojito with Crushed Sugarcane",
            "Blueberry Lavender Cooler"
        ]

    # 2. Appetizers & Salads
    if is_vegetarian:
        salads_and_starters = [
            "Crispy Vegetable & Paneer Spring Rolls with Sweet Chilli Dip",
            "Spicy Winged Bean (Dambala) & Gotukola Sambol with Grated Coconut",
            "Roasted Beetroot, Orange Segments & Crumbled Feta Salad",
            "Cashew Nut & Golden Corn Tartlets with Herb Mayo"
        ]
    else:
        salads_and_starters = [
            "Devilled Crispy Prawn Skewers with Sweet Garlic Glaze" if plate_budget >= 4500 else "Crispy Chicken & Sweet Corn Pastry",
            "Smoked Chicken & Hawaiian Pineapple Salad with Toasted Walnuts",
            "Traditional Sri Lankan Gotukola & Winged Bean Sambol",
            "Spicy Negombo Fish Cutlets with Tangy Chutney"
        ]

    # 3. Rice, Noodles & Breads
    starches = [
        "Fragrant Ghee Basmati Rice garnished with Fried Cashews and Caramelized Onions",
        "Steamed Fragrant Jasmine Rice",
        "Wok-tossed Vegetable Hakka Noodles with Spring Greens",
        "Freshly Baked Naan & Spiced Garlic Roti with Coriander Butter"
    ]

    # 4. Main Curries & Proteins
    if is_vegetarian:
        mains = [
            "Rich Creamy Kaju Maluwa (Sri Lankan Slow-cooked Cashew Nut Curry)",
            "Paneer Butter Masala with Fresh Kasuri Methi",
            "Devilled Button Mushroom with Capsicum and Banana Peppers",
            "Traditional Polos (Baby Jackfruit) Ambul Thiyal in Clay Pot",
            "Southern Style Dhal with Tempered Mustard & Curry Leaves",
            "Crispy Aubergine (Batu Moju) Sweet & Tangy Pickle"
        ]
    else:
        mains = [
            "Slow-braised Negombo Prawn Curry with Coconut Milk" if plate_budget >= 5000 else "Spicy Sri Lankan Claypot Chicken Curry",
            "Oven-roasted Pepper Beef Tenderloin / Ceylon Mutton Curry" if plate_budget >= 6000 else "Golden Butter Chicken with Fresh Cream",
            "Batter Fried Cuttlefish (Hot Butter Cuttlefish - HBC) with Spring Onions",
            "Rich Kaju (Cashew Nut) & Green Pea Curry in Coconut Gravy",
            "Traditional Polos (Baby Jackfruit) Curry",
            "Traditional Sweet & Sour Eggplant Moju (Batu Moju)"
        ]

    # 5. Desserts
    if is_lunch:
        desserts = [
            "Creamy Watalappam with Roasted Cashew Slivers & Kithul Treacle",
            "Chilled Tropical Fruit Salad with Coconut Ice Cream",
            "Passion Fruit Mousse Tartlets",
            "Mini Chocolate Fudge Brownies"
        ]
    else:
        desserts = [
            "Signature Steamed Watalappam with Rich Kithul Jaggery",
            "Caramel Pudding with Brandy Flambé Toffee Crunch",
            "Warm Chocolate Lava Cake with Vanilla Bean Gelato",
            "Assorted French Macarons & Strawberry Pavlova",
            "Traditional Curd (Meekiri) with Organic Sinharaja Kithul Treacle"
        ]

    # 6. Action Live Station (for Gold and Platinum tiers)
    live_stations: List[str] = []
    if plate_budget >= 4500.0:
        if is_vegetarian:
            live_stations.append("Live Kottu Station (Cheese Vegetable & Roti Kottu with Spiced Gravy)")
            live_stations.append("Live Hopper Station (Crispy Eggless String Hoppers & Plain Appa with Lunu Miris)")
        else:
            live_stations.append("Live Mongolian BBQ & Stir-fry Station (Chicken, Calamari, & Prawns)")
            live_stations.append("Live Traditional Hopper Counter (Egg Hoppers, Milk Hoppers, Cheese Hoppers)")

    result = {
        "status": "success",
        "menu_profile": {
            "tier": tier_name,
            "meal_slot": meal_slot,
            "dietary_preference": "Pure Vegetarian / Vegan" if is_vegetarian else "Standard (Poultry, Seafood & Meat - Halal Certified)",
            "budget_per_plate_lkr": float(plate_budget),
            "currency": "LKR"
        },
        "courses": {
            "welcome_drinks": welcome_drinks,
            "appetizers_and_salads": salads_and_starters,
            "rice_noodles_and_breads": starches,
            "main_dishes_and_curries": mains,
            "live_action_stations": live_stations if live_stations else ["Available on Gold & Platinum upgrades (4,500+ LKR/plate)"],
            "desserts": desserts,
            "after_meal_beverages": [
                "Freshly Brewed Ceylon BOP Tea with Cardamom & Ginger",
                "Roasted Sri Lankan Filter Coffee with Warm Dairy Milk"
            ]
        },
        "service_notes": {
            "service_style": "Grand Luxury Buffet with Dedicated Table Waiters",
            "culinary_standards": "All meats 100% Halal certified; no artificial food coloring or preservatives used.",
            "tasting_session": "Complimentary pre-wedding menu tasting session for 4 family members included."
        }
    }

    return convert_decimals(result)
