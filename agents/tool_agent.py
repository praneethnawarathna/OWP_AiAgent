import time
import logging
from typing import Dict, Any, List
from agents.state import GraphState

from tools.venue_tool import search_venues, search_all_category_vendors, find_venues_with_logistics
from tools.budget_tool import calculate_budget_and_installments
from tools.catering_tool import plan_catering_menu
from tools.theme_tool import generate_theme_package

logger = logging.getLogger("OleenaAIAgent")


def tool_agent_node(state: GraphState) -> Dict[str, Any]:
    """
    Node 3: Tool Agent Node (Deterministic PostgreSQL & Multi-Tool Suite / ZERO LLM calls):
    - Orchestrates all 4 modular tools from tools/:
      1. venue_tool
      2. catering_tool
      3. theme_tool
      4. budget_tool
    - Dynamic Intent & Category Filtering: If the user specifically requested a category
      (photography, hotel_venue, catering, decorations, music), queries and returns ONLY
      matching vendors and line items for that category.
    - Strict Price Ceiling Enforcement: If the user specified a max_price (e.g. 'below LKR 14000'),
      strictly enforces Price <= max_price in queries and never dumps out-of-budget vendors.
    - Strict Location Filtering: Eliminates cross-city leakage (e.g. vendors from Kotte never leak into Kandy).
    """
    t0 = time.time()
    traces = list(state.get("agent_traces") or [])

    location = state.get("location") or "Colombo"
    guest_count = int(state.get("guest_count") or 100)
    min_capacity = int(state.get("minimum_capacity") or guest_count)
    venue_budget_cap = float(state.get("allocated_venue_budget") or 800000.0)
    total_budget = float(state.get("budget") or 2000000.0)
    requested_category = state.get("requested_category")
    max_price = state.get("max_price")

    cat_label = requested_category.replace('_', ' ').title() if requested_category else "All 5 Categories"
    price_info = f", MaxPrice=LKR {max_price:,.2f}" if max_price else ""
    print("\n" + "-" * 80)
    print(f"[AGENT 3 - TOOL AGENT]: Executing dynamic tool queries for Category='{cat_label}', Location='{location}'{price_info}...")
    logger.info(f"[AGENT 3 - TOOL AGENT]: Executing dynamic tool queries for Category='{cat_label}', Location='{location}'{price_info}...")

    tools_used: List[str] = []

    # ── 1. Execute venue_tool ─────────────────────────────────────────────────
    print("[TOOL AGENT] Executing venue_tool...")
    logger.info("[TOOL AGENT] Executing venue_tool...")
    tools_used.append("tools.venue_tool.search_venues")
    venue_package = search_venues(
        location=location,
        min_capacity=min_capacity,
        max_budget=venue_budget_cap,
        max_price=max_price
    )
    venues_matched = venue_package.get("venues", [])

    all_category_services = search_all_category_vendors(
        location=location,
        min_capacity=min_capacity,
        max_price=max_price
    )

    # ── 2. Execute catering_tool ──────────────────────────────────────────────
    print("[TOOL AGENT] Executing catering_tool...")
    logger.info("[TOOL AGENT] Executing catering_tool...")
    tools_used.append("tools.catering_tool.plan_catering_menu")
    c_plate_target = round((total_budget * 0.30) / max(guest_count, 1), 2)
    catering_package = plan_catering_menu(
        budget_per_plate=c_plate_target,
        is_vegetarian=False,
        time_of_day="dinner"
    )
    c_profile = catering_package.get("menu_profile", {})

    # ── 3. Execute theme_tool ─────────────────────────────────────────────────
    print("[TOOL AGENT] Executing theme_tool...")
    logger.info("[TOOL AGENT] Executing theme_tool...")
    tools_used.append("tools.theme_tool.generate_theme_package")
    user_theme = "traditional"
    u_lower = (state.get("user_message") or "").lower()
    if any(k in u_lower for k in ["vintage", "retro", "classic"]):
        user_theme = "vintage"
    elif any(k in u_lower for k in ["lux", "modern", "glam"]):
        user_theme = "modern_luxury"
    elif any(k in u_lower for k in ["boho", "rustic", "garden"]):
        user_theme = "bohemian_rustic"
    theme_package = generate_theme_package(theme_name=user_theme)

    # ── 4. Execute budget_tool ────────────────────────────────────────────────
    print("[TOOL AGENT] Executing budget_tool...")
    logger.info("[TOOL AGENT] Executing budget_tool...")
    tools_used.append("tools.budget_tool.calculate_budget_and_installments")
    budget_package = calculate_budget_and_installments(total_budget=total_budget)
    categories = budget_package.get("category_breakdown", {})
    venue_cost = float(categories.get("hotel_and_venue", {}).get("allocated_amount_lkr", round(total_budget * 0.40, 2)))
    catering_cost = float(categories.get("catering_and_banquet", {}).get("allocated_amount_lkr", round(total_budget * 0.30, 2)))
    decorations_cost = float(categories.get("decorations_and_floral", {}).get("allocated_amount_lkr", round(total_budget * 0.10, 2)))
    photography_cost = float(categories.get("photography_and_video", {}).get("allocated_amount_lkr", round(total_budget * 0.15, 2)))
    music_cost = float(categories.get("music_and_entertainment", {}).get("allocated_amount_lkr", round(total_budget * 0.05, 2)))
    photo_music_cost = round(photography_cost + music_cost, 2)

    recommended_cards: List[Dict[str, Any]] = []
    line_items: List[Dict[str, Any]] = []
    selected_venue_name = state.get("selected_venue_name") or "Selected Venue"
    loc_clean = location.strip().lower()

    # ── BRANCH A: Photography Only ──────────────────────────────────────────
    if requested_category == "photography":
        print(f"[AGENT 3 - TOOL AGENT]: Filtering for Category 'Photography' in location='{location}' with max_price={max_price}...")
        tools_used.append("tools.venue_tool.search_all_category_vendors(category='photography')")
        photos = search_all_category_vendors(location=location, category_filter="photography", max_price=max_price)

        valid_photos = [
            p for p in photos
            if "ballroom" not in (p.get("serviceName") or "").lower()
            and "hall" not in (p.get("serviceName") or "").lower()
            and loc_clean in (p.get("city") or "").lower()
        ]
        if max_price is not None and max_price > 0:
            valid_photos = [p for p in valid_photos if float(p.get("price") or 0.0) <= max_price and float(p.get("price") or 0.0) > 0]

        if valid_photos:
            for idx, p in enumerate(valid_photos[:4]):
                p_price = float(p.get("price") or photography_cost)
                recommended_cards.append({
                    "id": int(p.get("serviceId") or (201 + idx)),
                    "serviceId": int(p.get("serviceId") or (201 + idx)),
                    "businessName": p.get("businessName") or "Oleena Photography",
                    "serviceName": p.get("serviceName") or "Cinematic 4K Wedding & Drone Coverage",
                    "category": "Photography",
                    "city": p.get("city") or location,
                    "price": p_price,
                    "capacity": None,
                    "imageUrl": p.get("imageUrl") or "https://images.unsplash.com/photo-1606800052052-a08af7148866?w=800",
                    "rating": 4.9,
                    "description": p.get("description") or "Full-day photo and 4K video ceremony coverage, album, and drone teaser."
                })

            primary_photo_cost = recommended_cards[0]["price"]
            total_estimate = primary_photo_cost
            primary_photo_name = recommended_cards[0]["serviceName"]
            primary_photo_biz = recommended_cards[0]["businessName"]

            line_items = [
                {
                    "category": "Photography",
                    "amount_lkr": primary_photo_cost,
                    "description": f"{primary_photo_name} by {primary_photo_biz} in {location}."
                }
            ]
        else:
            print(f"[AGENT 3 - TOOL AGENT]: No photography vendors matched price <= LKR {max_price} in {location}.")
            recommended_cards = []
            line_items = []
            total_estimate = 0.0

    # ── BRANCH B: Hotel / Venue Only ────────────────────────────────────────
    elif requested_category in ("hotel_venue", "venue"):
        print(f"[AGENT 3 - TOOL AGENT]: Filtering for Category 'Hotel / Venue' in location='{location}', min_capacity={min_capacity}, max_price={max_price}...")
        tools_used.append("tools.venue_tool.search_venues (Neon DB)")
        db_res = search_venues(
            location=location,
            min_capacity=min_capacity,
            max_budget=venue_budget_cap,
            max_price=max_price
        )
        venues_matched = [v for v in db_res.get("venues", []) if loc_clean in (v.get("city") or "").lower()]
        if max_price is not None and max_price > 0:
            venues_matched = [v for v in venues_matched if float(v.get("price") or 200000.0) <= max_price]

        if venues_matched:
            selected_venue_name = (
                venues_matched[0].get("serviceName")
                or venues_matched[0].get("businessName")
                or "Oleena Hotel Partner"
            )
            v_p = float(venues_matched[0].get("price") or 0.0)
            venue_rental_price = v_p if v_p > 0 else 200000.0

            for idx, v in enumerate(venues_matched[:4]):
                v_price = float(v.get("price") or venue_rental_price)
                if v_price <= 0:
                    v_price = venue_rental_price
                recommended_cards.append({
                    "id": int(v.get("serviceId") or v.get("vendorId") or (101 + idx)),
                    "serviceId": int(v.get("serviceId") or (101 + idx)),
                    "businessName": v.get("businessName") or "Oleena Hotel Partner",
                    "serviceName": v.get("serviceName") or "Grand Banquet Ballroom",
                    "category": "Hotel / Venue",
                    "city": v.get("city") or location,
                    "price": v_price,
                    "capacity": int(v.get("capacity") or min_capacity),
                    "imageUrl": v.get("imageUrl") or "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800",
                    "rating": 4.9,
                    "description": v.get("description") or f"Capacity up to {v.get('capacity', min_capacity)} guests with central AC and banquet facilities."
                })

            total_estimate = venue_rental_price
            line_items = [
                {
                    "category": "Hotel / Venue",
                    "amount_lkr": round(venue_rental_price, 2),
                    "description": f"Ballroom booking at {selected_venue_name} for {min_capacity} guest capacity."
                }
            ]
        else:
            print(f"[AGENT 3 - TOOL AGENT]: No venue spaces matched in {location}.")
            recommended_cards = []
            line_items = []
            total_estimate = 0.0

    # ── BRANCH C: Catering Only ─────────────────────────────────────────────
    elif requested_category == "catering":
        print(f"[AGENT 3 - TOOL AGENT]: Filtering for Category 'Catering' for {guest_count} guests...")
        tools_used.append("tools.catering_tool.plan_catering_menu")
        c_plate_user = round(total_budget / max(guest_count, 1), 2)
        if max_price is not None and max_price > 0:
            c_plate_user = max_price if max_price < 20000 else round(max_price / max(guest_count, 1), 2)

        c_data = plan_catering_menu(budget_per_plate=c_plate_user, is_vegetarian=False, time_of_day="dinner")
        cp = c_data["menu_profile"]
        total_c_estimate = round(cp["budget_per_plate_lkr"] * guest_count, 2)

        recommended_cards.append({
            "id": 501,
            "serviceId": 501,
            "businessName": "Oleena Grand Catering & Banquet Service",
            "serviceName": f"{cp['tier']} {cp['meal_slot']}",
            "category": "Catering",
            "city": location,
            "price": total_c_estimate,
            "capacity": guest_count,
            "imageUrl": "https://images.unsplash.com/photo-1555244162-803834f70033?w=800",
            "rating": 4.9,
            "description": f"{cp['tier']} banquet for {guest_count} guests @ LKR {cp['budget_per_plate_lkr']:,.0f}/plate. Includes welcome drinks, live action stations, and dessert buffet."
        })
        total_estimate = total_c_estimate
        line_items = [
            {
                "category": "Catering",
                "amount_lkr": total_c_estimate,
                "description": f"Complete {cp['tier']} banquet menu for {guest_count} guests."
            }
        ]

    # ── BRANCH D: Decorations Only ──────────────────────────────────────────
    elif requested_category == "decorations":
        print(f"[AGENT 3 - TOOL AGENT]: Filtering for Category 'Decorations' in location='{location}'...")
        tools_used.append("tools.venue_tool.search_all_category_vendors(category='decorations')")
        decors = search_all_category_vendors(location=location, category_filter="decorations", max_price=max_price)
        valid_decors = [d for d in decors if loc_clean in (d.get("city") or "").lower()]

        if valid_decors:
            for idx, d in enumerate(valid_decors[:4]):
                d_price = float(d.get("price") or decorations_cost)
                recommended_cards.append({
                    "id": int(d.get("serviceId") or (401 + idx)),
                    "serviceId": int(d.get("serviceId") or (401 + idx)),
                    "businessName": d.get("businessName") or "Oleena Florals & Decor",
                    "serviceName": d.get("serviceName") or "Luxury Floral & Stage Styling",
                    "category": "Decorations",
                    "city": d.get("city") or location,
                    "price": d_price,
                    "capacity": None,
                    "imageUrl": d.get("imageUrl") or "https://images.unsplash.com/photo-1519741497674-611481863552?w=800",
                    "rating": 4.9,
                    "description": d.get("description") or "Poruwa and reception floral styling."
                })
            primary_decor_cost = recommended_cards[0]["price"]
            total_estimate = primary_decor_cost
            line_items = [
                {
                    "category": "Decorations",
                    "amount_lkr": primary_decor_cost,
                    "description": f"Wedding floral styling by {recommended_cards[0]['businessName']}."
                }
            ]
        else:
            if max_price is not None and max_price > 0:
                recommended_cards = []
                line_items = []
                total_estimate = 0.0
            else:
                d_lineup = theme_package["vendor_lineup"]["decorator"]
                recommended_cards.append({
                    "id": 401,
                    "serviceId": 401,
                    "businessName": d_lineup["vendor_name"],
                    "serviceName": d_lineup["role"],
                    "category": "Decorations",
                    "city": location,
                    "price": decorations_cost,
                    "capacity": None,
                    "imageUrl": "https://images.unsplash.com/photo-1519741497674-611481863552?w=800",
                    "rating": 4.9,
                    "description": f"{d_lineup['aesthetic_elements']} Includes: {', '.join(d_lineup['inclusions'][:3])}."
                })
                total_estimate = decorations_cost
                line_items = [
                    {
                        "category": "Decorations",
                        "amount_lkr": decorations_cost,
                        "description": f"Themed styling by {d_lineup['vendor_name']}."
                    }
                ]

    # ── BRANCH E: Music Only ────────────────────────────────────────────────
    elif requested_category == "music":
        print(f"[AGENT 3 - TOOL AGENT]: Filtering for Category 'Music' in location='{location}'...")
        tools_used.append("tools.venue_tool.search_all_category_vendors(category='music')")
        musics = search_all_category_vendors(location=location, category_filter="music", max_price=max_price)
        valid_musics = [m for m in musics if loc_clean in (m.get("city") or "").lower()]

        if valid_musics:
            for idx, m in enumerate(valid_musics[:4]):
                m_price = float(m.get("price") or music_cost)
                recommended_cards.append({
                    "id": int(m.get("serviceId") or (301 + idx)),
                    "serviceId": int(m.get("serviceId") or (301 + idx)),
                    "businessName": m.get("businessName") or "Kandy DJ",
                    "serviceName": m.get("serviceName") or "Live Wedding Band & DJ",
                    "category": "Music",
                    "city": m.get("city") or location,
                    "price": m_price,
                    "capacity": None,
                    "imageUrl": m.get("imageUrl") or "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800",
                    "rating": 4.8,
                    "description": m.get("description") or "Live entertainment and sound system."
                })
            primary_music_cost = recommended_cards[0]["price"]
            total_estimate = primary_music_cost
            line_items = [
                {
                    "category": "Music",
                    "amount_lkr": primary_music_cost,
                    "description": f"Live music / DJ by {recommended_cards[0]['businessName']} in {location}."
                }
            ]
        else:
            if max_price is not None and max_price > 0:
                recommended_cards = []
                line_items = []
                total_estimate = 0.0
            else:
                m_lineup = theme_package["vendor_lineup"]["music_band"]
                recommended_cards.append({
                    "id": 301,
                    "serviceId": 301,
                    "businessName": m_lineup["vendor_name"],
                    "serviceName": m_lineup["role"],
                    "category": "Music",
                    "city": location,
                    "price": music_cost,
                    "capacity": None,
                    "imageUrl": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800",
                    "rating": 4.8,
                    "description": f"{m_lineup['genre']}. Inclusions: {', '.join(m_lineup['inclusions'][:2])}."
                })
                primary_music_cost = music_cost
                total_estimate = primary_music_cost
                line_items = [
                    {
                        "category": "Music",
                        "amount_lkr": primary_music_cost,
                        "description": f"Live entertainment and audio system by {recommended_cards[0]['businessName']}."
                    }
                ]

    # ── BRANCH F: General Wedding Planning (All 5 Categories) ───────────────
    else:
        print("[AGENT 3 - TOOL AGENT]: Orchestrating all 4 tools and Neon DB queries across all categories...")
        tools_used.extend([
            "tools.venue_tool.search_venues (Neon DB)",
            "tools.venue_tool.search_all_category_vendors (Neon DB)",
            "tools.budget_tool.calculate_budget_and_installments",
            "tools.catering_tool.plan_catering_menu",
            "tools.theme_tool.generate_theme_package"
        ])

        # 1. Venues (Strict location filtering, zero city leakage)
        strict_venues = [v for v in venues_matched if loc_clean in (v.get("city") or "").lower()]
        if strict_venues:
            selected_venue_name = (
                strict_venues[0].get("serviceName")
                or strict_venues[0].get("businessName")
                or "Oleena Hotel Partner"
            )
            v_p = float(strict_venues[0].get("price") or venue_cost)
            venue_actual_cost = v_p if v_p > 0 else venue_cost
            for idx, v in enumerate(strict_venues[:3]):
                price_val = float(v.get("price") or venue_actual_cost)
                recommended_cards.append({
                    "id": int(v.get("serviceId") or v.get("vendorId") or (101 + idx)),
                    "serviceId": int(v.get("serviceId") or (101 + idx)),
                    "businessName": v.get("businessName") or "Oleena Hotel Partner",
                    "serviceName": v.get("serviceName") or "Grand Banquet Ballroom",
                    "category": "Hotel / Venue",
                    "city": v.get("city") or location,
                    "price": price_val,
                    "capacity": int(v.get("capacity") or min_capacity),
                    "imageUrl": v.get("imageUrl") or "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800",
                    "rating": 4.9,
                    "description": v.get("description") or f"Capacity up to {v.get('capacity', min_capacity)} guests with banquet facilities."
                })
        else:
            selected_venue_name = f"Venue Allocation ({location})"
            venue_actual_cost = venue_cost

        # 2. Strict location matching for other vendor categories in Neon DB
        strict_category_services = [s for s in all_category_services if loc_clean in (s.get("city") or "").lower()]

        # Music (e.g. Kandy DJ)
        db_music = [s for s in strict_category_services if s.get("categoryId") == 3 or s.get("category") == "Music"]
        if db_music:
            for idx, m in enumerate(db_music[:2]):
                recommended_cards.append({
                    "id": int(m.get("serviceId") or (301 + idx)),
                    "serviceId": int(m.get("serviceId") or (301 + idx)),
                    "businessName": m.get("businessName") or "Kandy DJ",
                    "serviceName": m.get("serviceName") or "Live Wedding Band & DJ",
                    "category": "Music",
                    "city": m.get("city") or location,
                    "price": float(m.get("price") or music_cost),
                    "capacity": None,
                    "imageUrl": m.get("imageUrl") or "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800",
                    "rating": 4.8,
                    "description": m.get("description") or "Live DJ and sound reinforcement."
                })

        # Photography
        db_photos = [s for s in strict_category_services if (s.get("categoryId") == 2 or s.get("category") == "Photography") and "ballroom" not in (s.get("serviceName") or "").lower()]
        if db_photos:
            for idx, p in enumerate(db_photos[:2]):
                recommended_cards.append({
                    "id": int(p.get("serviceId") or (201 + idx)),
                    "serviceId": int(p.get("serviceId") or (201 + idx)),
                    "businessName": p.get("businessName") or "Wedding Photography",
                    "serviceName": p.get("serviceName") or "Cinematic Photography",
                    "category": "Photography",
                    "city": p.get("city") or location,
                    "price": float(p.get("price") or photography_cost),
                    "capacity": None,
                    "imageUrl": p.get("imageUrl") or "https://images.unsplash.com/photo-1606800052052-a08af7148866?w=800",
                    "rating": 4.9,
                    "description": p.get("description") or "Full wedding photo & video coverage."
                })

        # Decoration
        db_decor = [s for s in strict_category_services if s.get("categoryId") == 4 or "decor" in (s.get("serviceName") or "").lower()]
        if db_decor:
            for idx, d in enumerate(db_decor[:2]):
                recommended_cards.append({
                    "id": int(d.get("serviceId") or (401 + idx)),
                    "serviceId": int(d.get("serviceId") or (401 + idx)),
                    "businessName": d.get("businessName") or "Floral & Event Decor",
                    "serviceName": d.get("serviceName") or "Luxury Wedding Styling",
                    "category": "Decorations",
                    "city": d.get("city") or location,
                    "price": float(d.get("price") or decorations_cost),
                    "capacity": None,
                    "imageUrl": d.get("imageUrl") or "https://images.unsplash.com/photo-1519741497674-611481863552?w=800",
                    "rating": 4.9,
                    "description": d.get("description") or "Poruwa and reception floral styling."
                })

        # 3. Catering Package Card (from catering_tool)
        recommended_cards.append({
            "id": 501,
            "serviceId": 501,
            "businessName": "Oleena Grand Catering & Banquet Service",
            "serviceName": f"{c_profile.get('tier', 'Gold Premium')} {c_profile.get('meal_slot', 'Dinner Banquet')}",
            "category": "Catering",
            "city": location,
            "price": catering_cost,
            "capacity": guest_count,
            "imageUrl": "https://images.unsplash.com/photo-1555244162-803834f70033?w=800",
            "rating": 4.9,
            "description": f"{c_profile.get('tier', 'Gold Premium')} banquet for {guest_count} guests @ LKR {c_profile.get('budget_per_plate_lkr', c_plate_target):,.0f}/plate. Welcome drinks, live stations & dessert buffet."
        })

        # 4. Consolidate Line Items strictly matching the 4 required report categories
        line_items = [
            {
                "category": "Venue Allocation / Estimated Cost",
                "amount_lkr": venue_actual_cost,
                "description": f"Venue reservation allocation in {location} for {min_capacity} seats."
            },
            {
                "category": "Catering (per-plate calculation based on guest count)",
                "amount_lkr": catering_cost,
                "description": f"{guest_count} guests @ LKR {c_profile.get('budget_per_plate_lkr', c_plate_target):,.0f}/plate ({c_profile.get('tier', 'Gold Premium')} package)."
            },
            {
                "category": "Theme & Decoration",
                "amount_lkr": decorations_cost,
                "description": f"{theme_package.get('theme_display_name', 'Curated Theme & Floral Styling')} package."
            },
            {
                "category": "Photography & Music",
                "amount_lkr": photo_music_cost,
                "description": f"Photography & cinematography (LKR {photography_cost:,.2f}) and live music / DJ (LKR {music_cost:,.2f})."
            }
        ]

        total_estimate = round(
            venue_actual_cost + catering_cost + decorations_cost + photo_music_cost,
            2
        )

    print(f"[AGENT 3 - TOOL AGENT]: Tool execution complete. Compiled {len(recommended_cards)} cards for category '{cat_label}'. Total estimate: LKR {total_estimate:,.2f}.")
    logger.info(f"[AGENT 3 - TOOL AGENT]: Tool execution complete. Compiled {len(recommended_cards)} cards for category '{cat_label}'. Total estimate: LKR {total_estimate:,.2f}.")

    execution_time_ms = round((time.time() - t0) * 1000, 2)
    trace = {
        "step_name": "Node 3: Tool Agent (PostgreSQL & Multi-Tool Suite)",
        "status": "SUCCESS",
        "execution_time_ms": execution_time_ms,
        "output": {
            "requested_category": requested_category or "All Categories",
            "max_price": max_price,
            "cards_compiled_count": len(recommended_cards),
            "line_items_count": len(line_items),
            "total_estimate_lkr": total_estimate,
            "selected_venue": selected_venue_name,
            "tools_executed": tools_used
        }
    }
    traces.append(trace)

    return {
        "selected_venue_name": selected_venue_name,
        "line_items": line_items,
        "total_estimate": total_estimate,
        "recommended_vendors": recommended_cards,
        "requested_category": requested_category,
        "max_price": max_price,
        "venue_package": venue_package,
        "catering_package": catering_package,
        "theme_package": theme_package,
        "budget_package": budget_package,
        "agent_traces": traces
    }
