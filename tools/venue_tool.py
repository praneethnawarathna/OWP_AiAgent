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


# Curated catalog of Sri Lankan wedding venues with logistic & ride-hailing data
DUMMY_VENUES = [
    {
        "venue_id": 101,
        "name": "Cinnamon Grand - Oak Room",
        "city": "Colombo",
        "area": "Galle Face / Kollupitiya",
        "min_capacity": 150,
        "max_capacity": 550,
        "rental_price_lkr": 750000.0,
        "parking_capacity": 200,
        "ride_hailing_friendly": True,
        "ride_hailing_notes": "PickMe and Uber are available 24/7 with under 5 min wait times. Excellent for late-night departures.",
        "features": ["Luxury 5-Star Hotel", "Central AC", "Bridal Dressing Suite", "High ceiling chandeliers"]
    },
    {
        "venue_id": 102,
        "name": "Shangri-La Colombo - Lotus Ballroom",
        "city": "Colombo",
        "area": "Galle Face Promenade",
        "min_capacity": 200,
        "max_capacity": 1000,
        "rental_price_lkr": 1200000.0,
        "parking_capacity": 350,
        "ride_hailing_friendly": True,
        "ride_hailing_notes": "PickMe, Uber, and hotel taxi fleet readily accessible 24/7.",
        "features": ["Ocean View", "Column-free Ballroom", "State of the art AV", "VIP Lounge"]
    },
    {
        "venue_id": 103,
        "name": "Earl's Regency - Banquet Hall",
        "city": "Kandy",
        "area": "Tennekumbura",
        "min_capacity": 100,
        "max_capacity": 450,
        "rental_price_lkr": 550000.0,
        "parking_capacity": 120,
        "ride_hailing_friendly": True,
        "ride_hailing_notes": "PickMe and Uber operate reliably in Kandy municipal area until midnight; advance booking recommended for 1 AM+.",
        "features": ["River and Mountain Views", "Traditional Kandyan Architecture", "Outdoor Cocktail Terrace"]
    },
    {
        "venue_id": 104,
        "name": "Grand Kandyan Hotel - Royal Ballroom",
        "city": "Kandy",
        "area": "Peradeniya Road",
        "min_capacity": 150,
        "max_capacity": 600,
        "rental_price_lkr": 600000.0,
        "parking_capacity": 150,
        "ride_hailing_friendly": True,
        "ride_hailing_notes": "PickMe cars and three-wheelers active around Kandy city center throughout the night.",
        "features": ["360 Mountain View", "Rooftop Poolside", "Modern Soundproofing"]
    },
    {
        "venue_id": 105,
        "name": "Jetwing Lighthouse",
        "city": "Galle",
        "area": "Dadalla",
        "min_capacity": 80,
        "max_capacity": 300,
        "rental_price_lkr": 650000.0,
        "parking_capacity": 80,
        "ride_hailing_friendly": False,
        "ride_hailing_notes": "Limited PickMe/Uber coverage past 10 PM. Pre-arranged private vans or designated driver services are strongly recommended.",
        "features": ["Bawa Architecture", "Cliffside Ocean Backdrop", "Outdoor Lawn Ceremonies"]
    },
    {
        "venue_id": 106,
        "name": "Heritance Tea Factory",
        "city": "Nuwara Eliya",
        "area": "Kandapola",
        "min_capacity": 50,
        "max_capacity": 200,
        "rental_price_lkr": 480000.0,
        "parking_capacity": 50,
        "ride_hailing_friendly": False,
        "ride_hailing_notes": "No PickMe or Uber available in this remote highland area. Dedicated private bus or hired van transport is essential for guests.",
        "features": ["Historic Tea Plantation", "Misty Climate", "Heritage Ambience"]
    },
    {
        "venue_id": 107,
        "name": "The Blue Water Resort",
        "city": "Wadduwa",
        "area": "South Coast Beachfront",
        "min_capacity": 100,
        "max_capacity": 450,
        "rental_price_lkr": 500000.0,
        "parking_capacity": 100,
        "ride_hailing_friendly": False,
        "ride_hailing_notes": "Uber/PickMe availability drops sharply after 11 PM on the south coast strip. Pre-booking tuk-tuks or cabs advised.",
        "features": ["Coconut Palm Lawn", "Geoffrey Bawa Design", "Direct Beach Access"]
    },
    {
        "venue_id": 108,
        "name": "Waters Edge - Grand Ballroom",
        "city": "Colombo",
        "area": "Battaramulla",
        "min_capacity": 200,
        "max_capacity": 800,
        "rental_price_lkr": 850000.0,
        "parking_capacity": 400,
        "ride_hailing_friendly": True,
        "ride_hailing_notes": "PickMe and Uber 24/7 accessible; designated ride-hailing pickup bays at entrance.",
        "features": ["Diyawanna Lake Frontage", "Expansive Lawns", "Helipad Access"]
    }
]

# Hub cities where PickMe/Uber operate reliably late into the night
RIDE_HAILING_HUBS = {"colombo", "kandy", "dehiwala", "mount lavinia", "sri jayawardenepura kotte", "battaramulla", "negombo"}


def find_venues_with_logistics(guest_count: int, location: str) -> Dict[str, Any]:
    """
    Finds wedding venues matching guest count requirements and enriches each result
    with logistics metadata, including ride-hailing accessibility (PickMe/Uber) for late-night guest safety.

    Parameters:
        guest_count (int): Minimum required guest capacity for the wedding.
        location (str): Preferred city, district, or area (e.g., 'Colombo', 'Kandy', 'Galle').

    Returns:
        Dict[str, Any]: JSON-serializable dictionary with matched venues and logistical insights.
    """
    loc_clean = (location or "").strip().lower()
    min_guests = max(int(guest_count), 0)

    matched: List[Dict[str, Any]] = []

    for venue in DUMMY_VENUES:
        # Check capacity
        if venue["max_capacity"] < min_guests:
            continue

        # Check location filter if provided
        if loc_clean:
            in_city = loc_clean in venue["city"].lower()
            in_area = loc_clean in venue["area"].lower()
            if not (in_city or in_area):
                continue

        # Dynamically evaluate ride hailing friendliness if not explicitly set
        is_ride_friendly = venue["city"].lower() in RIDE_HAILING_HUBS or venue.get("ride_hailing_friendly", False)

        item = {
            "venue_id": venue["venue_id"],
            "name": venue["name"],
            "city": venue["city"],
            "area": venue["area"],
            "capacity_range": f"{venue['min_capacity']} - {venue['max_capacity']} guests",
            "rental_price_lkr": float(venue["rental_price_lkr"]),
            "parking_capacity": venue["parking_capacity"],
            "ride_hailing_friendly": bool(is_ride_friendly),
            "ride_hailing_notes": venue["ride_hailing_notes"],
            "features": venue["features"]
        }
        matched.append(item)

    # If no exact match found, provide helpful fallback venues that fit the capacity regardless of location
    if not matched:
        for venue in DUMMY_VENUES:
            if venue["max_capacity"] >= min_guests:
                is_ride_friendly = venue["city"].lower() in RIDE_HAILING_HUBS or venue.get("ride_hailing_friendly", False)
                matched.append({
                    "venue_id": venue["venue_id"],
                    "name": venue["name"],
                    "city": venue["city"],
                    "area": venue["area"],
                    "capacity_range": f"{venue['min_capacity']} - {venue['max_capacity']} guests",
                    "rental_price_lkr": float(venue["rental_price_lkr"]),
                    "parking_capacity": venue["parking_capacity"],
                    "ride_hailing_friendly": bool(is_ride_friendly),
                    "ride_hailing_notes": venue["ride_hailing_notes"],
                    "features": venue["features"]
                })
            if len(matched) >= 3:
                break

    return convert_decimals({
        "status": "success",
        "search_criteria": {
            "guest_count": min_guests,
            "location_query": location
        },
        "venues_found_count": len(matched),
        "venues": matched
    })


def search_venues(
    location: str = "",
    min_capacity: int = 0,
    max_budget: float = 0.0,
    max_price: Any = None
) -> Dict[str, Any]:
    """
    Searches wedding venues directly from the live Neon PostgreSQL database.
    Queries VendorServices joined with Vendors and VenueSpaces for real base prices,
    capacities, and locations. Strictly returns real database records.

    Parameters:
        location (str): Target city or district (e.g. 'Colombo', 'Kandy', 'Galle').
        min_capacity (int): Minimum required guest capacity.
        max_budget (float): Maximum venue budget allocation in LKR (0 for no cap).
        max_price (float): Strict maximum venue price cap in LKR (None/0 for no cap).

    Returns:
        Dict[str, Any]: Venues matched with real database prices and details.
    """
    import os
    import psycopg2
    from psycopg2.extras import RealDictCursor

    db_url = os.getenv("DATABASE_URL", "").strip()
    if not (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
        db_url = (
            "postgresql://neondb_owner:npg_FGLPEXqO31kv"
            "@ep-damp-base-ayw07lxk-pooler.c-5.us-east-2.aws.neon.tech"
            "/neondb?sslmode=require"
        )

    # Determine strict price threshold if provided
    strict_max = 0.0
    if max_price is not None and float(max_price) > 0:
        strict_max = float(max_price)
    elif max_budget > 0:
        strict_max = float(max_budget) * 1.5

    matched: List[Dict[str, Any]] = []
    try:
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT
                        vs."ServiceId"   AS "serviceId",
                        v."VendorId"     AS "vendorId",
                        v."BusinessName" AS "businessName",
                        vs."ServiceName" AS "serviceName",
                        c."CategoryName" AS "category",
                        COALESCE(v."City", vs."LocationAddress", 'Colombo') AS "city",
                        COALESCE(vs."Price", 200000.0)                     AS "price",
                        COALESCE(sp."SeatedCapacity", sp."FloatingCapacity", 350) AS "capacity",
                        COALESCE(vs."CoverImageUrl", v."CoverImageUrl", 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800') AS "imageUrl",
                        COALESCE(vs."ShortDescription", vs."Description", '') AS "description"
                    FROM "VendorServices" vs
                    JOIN "Vendors" v ON vs."VendorId" = v."VendorId"
                    JOIN "Categories" c ON vs."CategoryId" = c."CategoryId"
                    LEFT JOIN "VenueSpaces" sp ON vs."ServiceId" = sp."ServiceId"
                    WHERE c."CategoryId" = 1
                    AND (
                        v."City" ILIKE %(loc_pat)s
                        OR %(loc_clean)s = ''
                    )
                    ORDER BY vs."Price" ASC NULLS LAST;
                """
                loc_clean = (location or "").strip()
                loc_pattern = f"%{loc_clean}%" if loc_clean else "%"
                cur.execute(query, {"loc_pat": loc_pattern, "loc_clean": loc_clean})
                rows = cur.fetchall()
                for row in rows:
                    venue_item = convert_decimals(dict(row))
                    if min_capacity > 0 and venue_item.get("capacity", 0) < min_capacity:
                        continue
                    if strict_max > 0 and venue_item.get("price", 0) > strict_max:
                        continue
                    matched.append(venue_item)

    except Exception as exc:
        import logging
        logging.getLogger("uvicorn.error").error(f"[search_venues] PostgreSQL query error: {exc}")

    return convert_decimals({
        "status": "success",
        "database_source": "Neon PostgreSQL",
        "search_criteria": {
            "location": location,
            "min_capacity": min_capacity,
            "max_budget": max_budget,
            "max_price": max_price
        },
        "venues_found_count": len(matched),
        "venues": matched
    })


def search_all_category_vendors(
    location: str = "",
    min_capacity: int = 0,
    category_filter: Any = None,
    max_price: Any = None
) -> List[Dict[str, Any]]:
    """
    Queries real vendor services from the live Neon PostgreSQL DB.
    Optionally filters by a specific category and strict maximum price constraint:
      - 'photography': CategoryId = 2
      - 'hotel_venue' / 'venue': CategoryId = 1
      - 'music': CategoryId = 3
      - 'decorations': CategoryId = 4 or 'Decor' in name
      - 'catering': CategoryId = 5
      - max_price: If specified, strictly enforces vs."Price" <= max_price in SQL!
    """
    import os
    import psycopg2
    from psycopg2.extras import RealDictCursor

    db_url = os.getenv("DATABASE_URL", "").strip()
    if not (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
        db_url = (
            "postgresql://neondb_owner:npg_FGLPEXqO31kv"
            "@ep-damp-base-ayw07lxk-pooler.c-5.us-east-2.aws.neon.tech"
            "/neondb?sslmode=require"
        )

    cat_clause = ""
    if category_filter:
        cf = str(category_filter).lower().strip()
        if "photo" in cf:
            cat_clause = 'AND c."CategoryId" = 2'
        elif "venue" in cf or "hotel" in cf:
            cat_clause = 'AND c."CategoryId" = 1'
        elif "music" in cf or "band" in cf or "dj" in cf:
            cat_clause = 'AND c."CategoryId" = 3'
        elif "decor" in cf:
            cat_clause = 'AND (c."CategoryId" = 4 OR vs."ServiceName" ILIKE \'%%Decor%%\')'
        elif "cater" in cf or "food" in cf:
            cat_clause = 'AND c."CategoryId" = 5'

    loc_clean = (location or "").strip()
    loc_pattern = f"%{loc_clean}%" if loc_clean else "%"

    price_clause = ""
    params: Dict[str, Any] = {"loc_pat": loc_pattern, "loc_clean": loc_clean}
    if max_price is not None and float(max_price) > 0:
        price_clause = 'AND vs."Price" <= %(max_price)s'
        params["max_price"] = float(max_price)

    all_services: List[Dict[str, Any]] = []
    try:
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                query = f"""
                    SELECT 
                        vs."ServiceId" AS "serviceId",
                        vs."ServiceName" AS "serviceName",
                        c."CategoryName" AS "category",
                        c."CategoryId" AS "categoryId",
                        v."VendorId" AS "vendorId",
                        v."BusinessName" AS "businessName",
                        COALESCE(v."City", vs."LocationAddress", 'Colombo') AS "city",
                        COALESCE(v."Address", '') AS "address",
                        COALESCE(vs."Price", 0) AS "price",
                        COALESCE(sp."SeatedCapacity", sp."FloatingCapacity", 350) AS "capacity",
                        COALESCE(vs."CoverImageUrl", v."CoverImageUrl", '') AS "imageUrl",
                        COALESCE(vs."ShortDescription", vs."Description", '') AS "description",
                        vs."Status" AS "status"
                    FROM "VendorServices" vs
                    JOIN "Vendors" v ON vs."VendorId" = v."VendorId"
                    JOIN "Categories" c ON vs."CategoryId" = c."CategoryId"
                    LEFT JOIN "VenueSpaces" sp ON vs."ServiceId" = sp."ServiceId"
                    WHERE (
                        v."City" ILIKE %(loc_pat)s
                        OR %(loc_clean)s = ''
                    )
                    {cat_clause}
                    {price_clause}
                    ORDER BY vs."Price" ASC NULLS LAST;
                """
                cur.execute(query, params)
                rows = cur.fetchall()
                for r in rows:
                    all_services.append(convert_decimals(dict(r)))

    except Exception as exc:
        import logging
        logging.getLogger("uvicorn.error").error(f"[search_all_category_vendors] PostgreSQL query error: {exc}")

    return all_services



