"""
Package initialization for OWP AI Agent Function-Calling Tools.
Exports all 4 modular tools, their OpenAI-compatible schemas, and a tool dispatch map.
"""

from tools.budget_tool import calculate_budget_and_installments
from tools.venue_tool import find_venues_with_logistics, search_venues, search_all_category_vendors
from tools.theme_tool import generate_theme_package
from tools.catering_tool import plan_catering_menu

__all__ = [
    "calculate_budget_and_installments",
    "find_venues_with_logistics",
    "search_venues",
    "search_all_category_vendors",
    "generate_theme_package",
    "plan_catering_menu",
    "NEW_OPENAI_TOOLS",
    "NEW_TOOL_MAP",
]

# ─────────────────────────────────────────────────────────────────────────────
# OpenAI Tool Definitions (JSON Schema Array)
# ─────────────────────────────────────────────────────────────────────────────
NEW_OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_budget_and_installments",
            "description": (
                "Calculates an itemized wedding budget breakdown across Hotel (40%), Catering (30%), "
                "Photography (15%), Decorations (10%), and Music (5%). Also provides 3-month and 6-month "
                "Buy-Now-Pay-Later (BNPL) installment schedules (Koko/Mintpay style)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "total_budget": {
                        "type": "number",
                        "description": "Total wedding budget in Sri Lankan Rupees (LKR). Required."
                    }
                },
                "required": ["total_budget"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_venues_with_logistics",
            "description": (
                "Finds wedding venues and banquet halls matching guest capacity and location, "
                "with ride-hailing accessibility ratings (PickMe / Uber availability for late-night guest safety)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_count": {
                        "type": "integer",
                        "description": "Estimated or minimum guest count for the event. Required."
                    },
                    "location": {
                        "type": "string",
                        "description": "City, district, or area (e.g. 'Colombo', 'Kandy', 'Galle'). Required."
                    }
                },
                "required": ["guest_count", "location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_theme_package",
            "description": (
                "Generates a cohesive, theme-based vendor bundle combining a Photographer, "
                "Concept Decorator, and Music Band with unified package discounts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "theme_name": {
                        "type": "string",
                        "description": "Desired wedding theme or style (e.g. 'Traditional', 'Vintage', 'Modern Luxury', 'Bohemian', 'Rustic'). Required."
                    }
                },
                "required": ["theme_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plan_catering_menu",
            "description": (
                "Designs a complete multi-course wedding catering menu based on budget per plate, "
                "dietary preference (vegetarian vs non-vegetarian), and event timing (lunch vs dinner)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_per_plate": {
                        "type": "number",
                        "description": "Target catering budget per plate/head in Sri Lankan Rupees (LKR). Required."
                    },
                    "is_vegetarian": {
                        "type": "boolean",
                        "description": "True if pure vegetarian/vegan menu is requested, false for standard non-vegetarian menu."
                    },
                    "time_of_day": {
                        "type": "string",
                        "description": "Timing of the event: 'lunch' (afternoon) or 'dinner' (evening/night).",
                        "enum": ["lunch", "dinner"]
                    }
                },
                "required": ["budget_per_plate"]
            }
        }
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher Map: tool name -> Python callable
# ─────────────────────────────────────────────────────────────────────────────
NEW_TOOL_MAP = {
    "calculate_budget_and_installments": calculate_budget_and_installments,
    "find_venues_with_logistics": find_venues_with_logistics,
    "generate_theme_package": generate_theme_package,
    "plan_catering_menu": plan_catering_menu,
}
