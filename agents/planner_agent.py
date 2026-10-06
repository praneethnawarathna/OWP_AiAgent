import os
import re
import json
import time
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from agents.state import GraphState

logger = logging.getLogger("OleenaAIAgent")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "auto").strip() or "auto"

SRI_LANKA_CITIES = [
    "colombo", "kandy", "galle", "negombo", "nuwara eliya", "wadduwa",
    "bentota", "battaramulla", "dehiwala", "kotte", "mount lavinia",
    "jaffna", "matara", "kalutara", "anuradhapura", "kurunegala", "gampaha",
    "beruwala", "panadura", "moratuwa", "ratnapura"
]


def get_openai_client() -> OpenAI:
    """Initializes and returns an OpenAI client configured for custom or official endpoints."""
    base_url = OPENAI_BASE_URL
    if base_url and not base_url.endswith("/v1"):
        base_url = f"{base_url.rstrip('/')}/v1"

    return OpenAI(
        api_key=OPENAI_API_KEY or "dummy-key",
        base_url=base_url if base_url else None
    )


def _extract_budget_amount(text: str) -> Optional[float]:
    """
    Extracts total budget specifications and dynamic adjustments from user messages.
    Handles phrases like:
      - 'My budget is LKR 1,200,000'
      - 'Adjust budget to 1M', 'budget is 1.5 million', 'budget of 800k'
      - 'budget is 1200000', '1.2M budget'
      - 'budget 1500000 LKR'
    """
    if not text:
        return None
    t = text.lower().replace(",", "")

    # 1. 'budget' followed by amount: 'budget is 1.2m', 'budget: 1200000', 'budget to 1m', 'budget of 1.5 million'
    mA = re.search(r'\bbudget\s*(?:is|to|of|around|about|limit|cap|:)?\s*(?:lkr|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(k|m|million|lakh|crore)?\b', t)
    if mA:
        val = float(mA.group(1))
        unit = mA.group(2)
        if unit == 'k':
            val *= 1000
        elif unit in ('m', 'million'):
            val *= 1000000
        elif unit == 'lakh':
            val *= 100000
        elif unit == 'crore':
            val *= 10000000
        if val > 1000:
            return val

    # 2. Amount followed by 'budget': '1.2m budget', '1m budget', '1200000 budget'
    mB = re.search(r'\b(?:lkr|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(k|m|million|lakh)?\s*(?:lkr|rupees)?\s*budget\b', t)
    if mB:
        val = float(mB.group(1))
        unit = mB.group(2)
        if unit == 'k':
            val *= 1000
        elif unit in ('m', 'million'):
            val *= 1000000
        elif unit == 'lakh':
            val *= 100000
        if val > 1000:
            return val

    # 3. Currency followed by high amount: 'LKR 1,200,000', 'Rs. 1500000'
    mC = re.search(r'(?:lkr|rs\.?)\s*(\d{5,}(?:\.\d+)?)\b', t)
    if mC:
        return float(mC.group(1))

    return None


def _fallback_extract_entities(text: str) -> Dict[str, Any]:
    """
    Deterministic Python regex entity extractor used as a robust fallback
    if the LLM output fails JSON parsing or omits parameters.
    """
    if not text:
        return {"location": None, "guest_count": None, "budget": None}

    text_lower = text.lower()
    loc = None
    for city in SRI_LANKA_CITIES:
        if city in text_lower:
            loc = city.title()
            break

    guests = None
    guest_match = re.search(r'(\d{2,4})\s*(?:guests?|people|pax|heads?|invitees?)', text_lower)
    if guest_match:
        try:
            guests = int(guest_match.group(1))
        except (ValueError, TypeError):
            pass
    else:
        standalone = re.search(r'(?:^|\b)(?:for\s+)?(\d{2,4})\b', text_lower)
        if standalone:
            try:
                val = int(standalone.group(1))
                if 20 <= val <= 3500:
                    guests = val
            except (ValueError, TypeError):
                pass

    budget = _extract_budget_amount(text_lower)

    return {"location": loc, "guest_count": guests, "budget": budget}


def _detect_category_intent(text: str) -> Optional[str]:
    """
    Detects if the user specifically requested a single vendor category.
    """
    if not text:
        return None
    t = text.lower()
    if re.search(r'\b(photo|photograph|photographer|photography|videography|cinematography|photoshoot|album|camera)\b', t):
        return "photography"
    if re.search(r'\b(venue|hotel|hall|ballroom|banquet|resort)\b', t):
        return "hotel_venue"
    if re.search(r'\b(cater|catering|caterer|food|buffet|menu|meal|dinner|lunch|plate)\b', t):
        return "catering"
    if re.search(r'\b(decor|decoration|decorator|floral|flowers|poruwa|stage decor|setty back)\b', t):
        return "decorations"
    if re.search(r'\b(music|band|dj|sound system|singers|live band)\b', t):
        return "music"
    return None


def _extract_max_price(text: str) -> Optional[float]:
    """
    Extracts explicit price ceilings or maximum budget caps specified by the user.
    """
    if not text:
        return None
    t = text.lower().replace(",", "")

    # 1. Phrases with leading keywords: below, under, less than, cheaper than, within, max, maximum, budget
    pattern1 = r'\b(?:below|under|less\s+than|cheaper\s+than|within|max(?:imum)?(?:\s+(?:price|budget|rate|fee))?|budget(?:\s+(?:under|below|limit|of|cap))?)\s*(?:lkr|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(k|m|million|lakh)?\b'
    m1 = re.search(pattern1, t)
    if m1:
        val = float(m1.group(1))
        unit = m1.group(2)
        if unit == 'k':
            val *= 1000
        elif unit in ('m', 'million'):
            val *= 1000000
        elif unit == 'lakh':
            val *= 100000
        return val

    # 2. Trailing keywords: e.g. "14000 max", "50k budget limit", "20000 or less"
    pattern2 = r'\b(?:lkr|rs\.?)?\s*(\d+(?:\.\d+)?)\s*(k)?\s*(?:max|maximum|or\s+less|budget\s+limit|cap)\b'
    m2 = re.search(pattern2, t)
    if m2:
        val = float(m2.group(1))
        if m2.group(2) == 'k':
            val *= 1000
        return val

    return None


def planner_node(state: GraphState) -> Dict[str, Any]:
    """
    Node 1: Planner Agent (LLM Engine):
    Uses the OpenAI-compatible API to extract structured location, guest_count,
    budget, max_price, and category intent from the user's message.
    """
    t0 = time.time()
    user_msg = (state.get("user_message") or "").strip()
    traces = list(state.get("agent_traces") or [])

    print("\n" + "=" * 80)
    print("[AGENT 1 - PLANNER]: Analyzing intent and extracting parameters with LLM...")
    logger.info("[AGENT 1 - PLANNER]: Analyzing intent and extracting parameters with LLM...")

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured in the environment. Agent 1 requires a valid OpenAI API key.")

    client = get_openai_client()

    system_instruction = (
        "You are a strict data extraction engine for a wedding planning system in Sri Lanka.\n"
        "Your ONLY job is to extract the intended wedding location, guest count, any requested vendor category, and any explicit maximum price/budget constraint from the user's message.\n"
        "Return ONLY a raw JSON object with exactly these keys:\n"
        '{"location": string or null, "guest_count": integer or null, "budget": number or null, "max_price": number or null, "requested_category": string or null}\n'
        "RULES:\n"
        "- 'location': The city or district in Sri Lanka (e.g., 'Colombo', 'Kandy', 'Galle', 'Negombo') or null if not provided.\n"
        "- 'guest_count': The integer number of guests or null if not provided.\n"
        "- 'budget': The total wedding budget in LKR or null if not provided.\n"
        "- 'max_price': If user specifies a price ceiling or budget limit (e.g., 'below LKR 14000', 'under 14000', 'under 50k', 'less than 20000', 'budget 15000'), extract it as a numeric value in LKR (e.g. 14000, 50000). Otherwise null.\n"
        "- 'requested_category': If user asks for a specific vendor type, specify one of: 'photography', 'hotel_venue', 'catering', 'decorations', 'music'. Return null if planning full wedding.\n"
        "- Do NOT output markdown code blocks (no ```json). Do NOT output conversational text, explanations, or backticks. Return ONLY the raw JSON object."
    )

    extracted: Dict[str, Any] = {}
    raw_response_text = ""

    try:
        api_messages = [{"role": "system", "content": system_instruction}]

        history = state.get("conversation_messages") or []
        for h in history[-4:]:
            role = h.get("role", "user")
            content = str(h.get("content", "")).strip()
            if role in ("user", "assistant") and content:
                api_messages.append({"role": role, "content": content})

        if not history or history[-1].get("content") != user_msg:
            api_messages.append({"role": "user", "content": user_msg})

        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=api_messages,
                temperature=0.0
            )
        except Exception as model_err:
            if "model_not_found" in str(model_err).lower() or "not in the catalog" in str(model_err).lower():
                response = client.chat.completions.create(
                    model="auto",
                    messages=api_messages,
                    temperature=0.0
                )
            else:
                raise model_err

        raw_response_text = (response.choices[0].message.content or "").strip()

        json_match = re.search(r"\{.*?\}", raw_response_text, re.DOTALL)
        if json_match:
            try:
                extracted = json.loads(json_match.group(0))
            except Exception as json_err:
                logger.warning(f"[Planner Node] Regex JSON parse error: {json_err}. Raw text: {raw_response_text}")

        if not extracted:
            cleaned = re.sub(r"^```(?:json)?\s*|```\s*$", "", raw_response_text, flags=re.MULTILINE).strip()
            extracted = json.loads(cleaned)

    except Exception as e:
        logger.warning(f"[Planner Node] LLM parsing issue: {e}. Executing graceful regex fallback.")

    # Parameter consolidation
    fallback = _fallback_extract_entities(user_msg)

    # 1. Location
    location = state.get("location") or extracted.get("location") or fallback.get("location")
    if location and str(location).lower() in ("null", "none"):
        location = None
    if location:
        location = str(location).strip().title()

    # 2. Guest Count
    guest_count = state.get("guest_count") or extracted.get("guest_count") or fallback.get("guest_count")
    if guest_count:
        try:
            guest_count = int(guest_count)
        except (ValueError, TypeError):
            guest_count = None

    # 3. Budget (Prioritize explicit budget in current user message)
    user_budget = _extract_budget_amount(user_msg)
    llm_budget = extracted.get("budget")
    if llm_budget:
        try:
            llm_budget = float(llm_budget)
        except (ValueError, TypeError):
            llm_budget = None

    budget = user_budget or llm_budget or state.get("budget") or fallback.get("budget")
    if budget:
        try:
            budget = float(budget)
        except (ValueError, TypeError):
            budget = None

    # 4. Strict Price Ceiling (max_price)
    user_max_price = _extract_max_price(user_msg)
    llm_max_price = extracted.get("max_price")
    max_price = user_max_price or llm_max_price or state.get("max_price")
    if max_price:
        try:
            max_price = float(max_price)
        except (ValueError, TypeError):
            max_price = None

    # Multi-turn history retrieval for missing parameters
    for prev in reversed(state.get("conversation_messages") or []):
        if prev.get("role") in ("user", "human"):
            prev_text = str(prev.get("content", ""))
            prev_fb = _fallback_extract_entities(prev_text)
            if not location and prev_fb.get("location"):
                location = prev_fb["location"]
            if not guest_count and prev_fb.get("guest_count"):
                guest_count = prev_fb["guest_count"]
            if not budget and _extract_budget_amount(prev_text):
                budget = _extract_budget_amount(prev_text)
            if not max_price and _extract_max_price(prev_text):
                max_price = _extract_max_price(prev_text)

    # 5. Category Intent Detection
    if re.search(r'\b(all categories|all vendors|full package|entire wedding|everything|whole wedding)\b', user_msg.lower()):
        requested_category = None
    else:
        detected_cat = _detect_category_intent(user_msg)
        llm_cat = extracted.get("requested_category")
        if llm_cat and str(llm_cat).lower() in ("null", "none", "all", ""):
            llm_cat = None
        requested_category = detected_cat or llm_cat or state.get("requested_category")
    if requested_category and str(requested_category).lower() in ("null", "none", "all", ""):
        requested_category = None
    if requested_category:
        rc_lower = str(requested_category).lower()
        if "photo" in rc_lower:
            requested_category = "photography"
        elif "venue" in rc_lower or "hotel" in rc_lower or "hall" in rc_lower:
            requested_category = "hotel_venue"
        elif "cater" in rc_lower or "food" in rc_lower:
            requested_category = "catering"
        elif "decor" in rc_lower:
            requested_category = "decorations"
        elif "music" in rc_lower or "band" in rc_lower or "dj" in rc_lower:
            requested_category = "music"

    if requested_category in ("photography", "music", "decorations") and not guest_count:
        guest_count = 150

    # 6. Check greeting & missing parameters
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "ayubowan"}
    clean_msg = re.sub(r"[^\w\s]", "", user_msg.lower()).strip()
    is_greeting = clean_msg in greetings or (not location and not guest_count and not requested_category and len(clean_msg) < 8)

    missing = []
    if not location:
        missing.append("location")
    if not guest_count and not requested_category:
        missing.append("guest_count")

    requires_clarification = is_greeting or bool(missing)

    conversational_reply = ""
    if requires_clarification:
        if is_greeting:
            conversational_reply = (
                "Hello! Welcome to Oleena Wedding Planner. I would be delighted to assist in planning your wedding. "
                "Could you please share your preferred wedding location (e.g., Colombo, Kandy, Galle) and estimated guest count?"
            )
        elif "location" in missing and requested_category:
            cat_label = requested_category.replace("_", " ").title()
            conversational_reply = (
                f"Which city or district in Sri Lanka would you like to explore {cat_label} vendors in (e.g., Colombo, Kandy, Galle)?"
            )
        elif "location" in missing and "guest_count" in missing:
            conversational_reply = (
                "To help find the right venues and compute an accurate itemized estimate, "
                "could you please share your preferred wedding location in Sri Lanka and your estimated guest count?"
            )
        elif "location" in missing:
            conversational_reply = (
                f"We noted a guest count of {guest_count}. Which city or district in Sri Lanka would you like to host your wedding in "
                "(e.g., Colombo, Kandy, Galle)?"
            )
        elif "guest_count" in missing:
            conversational_reply = (
                f"Great, we will search for wedding venues in {location}! How many guests are you expecting?"
            )

    execution_time_ms = round((time.time() - t0) * 1000, 2)

    planner_trace = {
        "step_name": "Node 1: Planner Agent (LLM)",
        "status": "PAUSED" if requires_clarification else "SUCCESS",
        "execution_time_ms": execution_time_ms,
        "output": {
            "is_greeting": is_greeting,
            "extracted_location": location,
            "extracted_guest_count": guest_count,
            "extracted_budget": budget,
            "extracted_max_price": max_price,
            "extracted_category": requested_category,
            "missing_parameters": missing,
            "requires_clarification": requires_clarification,
            "raw_llm_response": raw_response_text[:120] if raw_response_text else "fallback_used"
        }
    }
    traces.append(planner_trace)

    if requires_clarification:
        print(f"[AGENT 1 - PLANNER]: Missing parameters: {missing}. Pausing workflow for user clarification.")
        logger.info(f"[AGENT 1 - PLANNER]: Missing parameters: {missing}. Pausing workflow for user clarification.")
        return {
            "location": location,
            "guest_count": guest_count,
            "budget": budget,
            "max_price": max_price,
            "requested_category": requested_category,
            "missing_parameters": missing,
            "workflow_status": "NeedsClarification",
            "ai_reply_message": conversational_reply,
            "agent_traces": traces,
            "confidence_score": 0.0 if is_greeting else 0.25,
            "total_estimate": 0.0,
            "requires_approval": False,
        }

    cat_label = requested_category.replace('_', ' ').title() if requested_category else 'Full Package'
    print(f"[AGENT 1 - PLANNER]: Extracted parameters -> Location='{location}', Guests={guest_count}, Budget={budget}, MaxPrice={max_price}, CategoryIntent='{cat_label}'")
    print("[AGENT 1 - PLANNER]: Parameter verification passed. Routing to Domain Analyst.")
    logger.info(f"[AGENT 1 - PLANNER]: Extracted parameters -> Location='{location}', Guests={guest_count}, Budget={budget}, MaxPrice={max_price}, CategoryIntent='{cat_label}'")

    return {
        "location": str(location).strip(),
        "guest_count": int(guest_count),
        "budget": float(budget) if budget else 2000000.0,
        "max_price": max_price,
        "requested_category": requested_category,
        "missing_parameters": missing,
        "workflow_status": "In_Progress",
        "ai_reply_message": f"Planning verified for {guest_count} guests in {location}.",
        "agent_traces": traces,
        "confidence_score": 0.90 if not budget else 1.0,
    }


def check_parameters_condition(state: GraphState) -> str:
    """
    Conditional Edge Router:
    - If parameters are missing or status is 'NeedsClarification', route to END.
    - Otherwise, route to Node 2: Domain Analyst.
    """
    if state.get("workflow_status") == "NeedsClarification":
        return "end"
    if not state.get("location") or not state.get("guest_count"):
        return "end"
    return "domain_analyst"
