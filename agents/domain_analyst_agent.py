import time
import logging
from typing import Dict, Any
from agents.state import GraphState

logger = logging.getLogger("OleenaAIAgent")


def domain_analyst_node(state: GraphState) -> Dict[str, Any]:
    """
    Node 2: Domain Analyst Node (Pure Python / ZERO LLM calls):
    - Computes venue capacity requirement with a 15% safety buffer.
    - Applies spatial and geographic radius filtering rules.
    - Determines venue budget allocation (40% industry standard).
    """
    t0 = time.time()
    traces = list(state.get("agent_traces") or [])

    print("\n" + "-" * 80)
    print("[AGENT 2 - DOMAIN ANALYST]: Starting spatial and capacity requirement analysis...")
    logger.info("[AGENT 2 - DOMAIN ANALYST]: Starting spatial and capacity requirement analysis...")

    guest_count = state["guest_count"]
    buffer_percentage = 15.0
    minimum_capacity = int(guest_count * (1.0 + (buffer_percentage / 100.0)))

    loc = (state.get("location") or "Colombo").strip().title()
    loc_lower = loc.lower()

    if any(k in loc_lower for k in ["colombo", "battaramulla", "dehiwala", "kotte", "mount lavinia"]):
        geo_zone = "Western Metropolitan District"
        search_radius_km = 25
    elif any(k in loc_lower for k in ["kandy", "peradeniya", "tennekumbura"]):
        geo_zone = "Central Highlands District"
        search_radius_km = 30
    elif any(k in loc_lower for k in ["galle", "bentota", "wadduwa", "hikkaduwa"]):
        geo_zone = "Southern Coastal Corridor"
        search_radius_km = 40
    else:
        geo_zone = "Regional Islandwide Zone"
        search_radius_km = 50

    total_budget = state.get("budget") or 2000000.0
    allocated_venue_budget = round(total_budget * 0.40, 2)

    print(f"[AGENT 2 - DOMAIN ANALYST]: Applied {buffer_percentage}% safety buffer -> Minimum Capacity: {minimum_capacity} seats.")
    print(f"[AGENT 2 - DOMAIN ANALYST]: Geographic zone resolved to '{geo_zone}' (Radius: {search_radius_km} km, Allocated Venue Budget: LKR {allocated_venue_budget:,.2f}).")
    print("[AGENT 2 - DOMAIN ANALYST]: Domain analysis completed. Passing state to Tool Agent.")
    logger.info("[AGENT 2 - DOMAIN ANALYST]: Domain analysis completed. Passing state to Tool Agent.")

    execution_time_ms = round((time.time() - t0) * 1000, 2)
    trace = {
        "step_name": "Node 2: Domain Analyst Agent",
        "status": "SUCCESS",
        "execution_time_ms": execution_time_ms,
        "output": {
            "target_guest_count": guest_count,
            "minimum_capacity_required": minimum_capacity,
            "capacity_buffer_percentage": buffer_percentage,
            "geo_zone": geo_zone,
            "search_radius_km": search_radius_km,
            "allocated_venue_budget_lkr": allocated_venue_budget
        }
    }
    traces.append(trace)

    return {
        "budget": total_budget,
        "minimum_capacity": minimum_capacity,
        "capacity_buffer_percentage": buffer_percentage,
        "geo_zone": geo_zone,
        "search_radius_km": search_radius_km,
        "allocated_venue_budget": allocated_venue_budget,
        "requested_category": state.get("requested_category"),
        "max_price": state.get("max_price"),
        "agent_traces": traces
    }
