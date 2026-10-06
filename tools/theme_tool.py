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


# Curated vendor packages tailored for popular Sri Lankan wedding themes
THEME_PRESETS = {
    "traditional": {
        "theme_display_name": "Traditional Kandyan & Heritage Elegance",
        "description": "Authentic Sri Lankan cultural celebration with handcrafted wooden Poruwa, Magul Bera, and heritage styling.",
        "photographer": {
            "vendor_name": "Studio Heritage Moments",
            "lead_specialist": "Duminda Ranasinghe",
            "style": "Classic portraiture and cultural ceremony documentation",
            "includes": ["Traditional Poruwa ceremony coverage", "Family portraits", "Bridal party in Osariya/Nilame attire", "2 Leather storybooks", "Drone footage"],
            "individual_price_lkr": 380000.0
        },
        "decorator": {
            "vendor_name": "Mayura Floral & Poruwa Creations",
            "lead_stylist": "Chathuri Alahakoon",
            "style_elements": "Handcrafted wooden Poruwa with brass oil lamps (Pahana), Pun Kalas, fresh lotus blooms, jasmine garlands, and gold drapery.",
            "includes": ["Carved Wooden Poruwa", "Traditional Entrance Torana", "Oil Lamp display", "60 Table floral centerpieces", "Setty back & Head table"],
            "individual_price_lkr": 480000.0
        },
        "music_band": {
            "vendor_name": "Rhythm of Lanka & The Heritage Ensemble",
            "genre": "Traditional Magul Bera, flute prelude, followed by 5-piece acoustic folk & Sinhala evergreen classics",
            "includes": ["Traditional drummers & Jayamangala Gatha ensemble", "Acoustic 5-piece live band for dinner reception", "Sound system and microphones"],
            "individual_price_lkr": 220000.0
        },
        "bundle_discount_percent": 10.0
    },
    "vintage": {
        "theme_display_name": "Vintage Colonial Romance",
        "description": "Nostalgic retro charm inspired by Ceylon's heritage architecture, lace accents, muted pastels, and vintage jazz/swing.",
        "photographer": {
            "vendor_name": "Sepia & Silk Cinematic Studio",
            "lead_specialist": "Rohan Perera",
            "style": "Moody film aesthetics, warm sepia tones, and natural candid moments",
            "includes": ["Vintage film look grading", "Pre-shoot with classic Austin Cambridge car", "Full day coverage", "Custom linen photo album", "Cinematic highlight reel"],
            "individual_price_lkr": 420000.0
        },
        "decorator": {
            "vendor_name": "Old Ceylon Bloom & Decor",
            "lead_stylist": "Nalaka Senanayake",
            "style_elements": "Weathered timber arches, fairy lights, antique phonographs, brass candelabras, baby's breath, and blush garden roses.",
            "includes": ["Antique archway entrance", "Rustic wooden head table", "Candelabra centerpieces with fairy lights", "Vintage photo booth lounge with antique furniture"],
            "individual_price_lkr": 450000.0
        },
        "music_band": {
            "vendor_name": "The Colombo Jazz Quartet & Swing Society",
            "genre": "Retro 60s/70s Jazz, Blues, Frank Sinatra & Vintage Baila",
            "includes": ["Live brass section (Saxophone, Trumpet)", "Upright bass and jazz drums", "4-hour reception entertainment with bespoke first dance track"],
            "individual_price_lkr": 260000.0
        },
        "bundle_discount_percent": 10.0
    },
    "modern_luxury": {
        "theme_display_name": "Modern Luxury & Glamour",
        "description": "Sleek, opulent metropolitan aesthetics featuring mirror walkways, crystal chandeliers, white orchids, and high-energy live performance.",
        "photographer": {
            "vendor_name": "Lumina High-Fashion Weddings",
            "lead_specialist": "Tanya Gunawardena",
            "style": "Vogue editorial fashion photography, high-dynamic cinematic 4K video",
            "includes": ["3-camera crew", "4K drone", "Same-day edit video teaser", "Fine-art acrylic photo album", "Glamour studio portrait booth"],
            "individual_price_lkr": 520000.0
        },
        "decorator": {
            "vendor_name": "Crystal & Flora Grand Stylists",
            "lead_stylist": "Shanaka Jayasuriya",
            "style_elements": "Mirrored stage, hanging floral ceiling canopy with imported white orchids, acrylic tables, moving-head intelligent lighting.",
            "includes": ["100-foot mirrored aisle", "Suspended ceiling floral installation", "Acrylic bride & groom dais", "Intelligent stage lighting trusses"],
            "individual_price_lkr": 750000.0
        },
        "music_band": {
            "vendor_name": "Flame & Synergy Live 7-Piece Band + DJ",
            "genre": "Top 40 Pop, Rock, Sinhala/English Commercial Hits & Late Night DJ Set",
            "includes": ["7-piece live band with 3 vocalists", "Club DJ for after-party", "Digital line-array concert audio & haze machines"],
            "individual_price_lkr": 380000.0
        },
        "bundle_discount_percent": 12.0
    },
    "bohemian_rustic": {
        "theme_display_name": "Rustic Bohemian Chic",
        "description": "Earthy, free-spirited vibe with pampas grass, warm sunset tones, macramé details, and relaxed acoustic melodies.",
        "photographer": {
            "vendor_name": "Wildflower Stories SL",
            "lead_specialist": "Kaveen De Silva",
            "style": "Golden hour warmth, candid documentary storytelling",
            "includes": ["Golden hour portraits", "Full day candid coverage", "Handcrafted pine keepsake box with prints", "Super-8 style digital retro video"],
            "individual_price_lkr": 360000.0
        },
        "decorator": {
            "vendor_name": "Boho Blooms & Driftwood Art",
            "lead_stylist": "Ananya Peiris",
            "style_elements": "Dried pampas grass, terracotta urns, geometric wooden teepee altar, Edison bulbs, jute rugs, and eucalyptus runners.",
            "includes": ["Geometric wooden wedding altar", "Boho bridal backdrop with macramé", "Fairy light canopy over lawn/ballroom", "40 Tables with terracotta & dried flora"],
            "individual_price_lkr": 400000.0
        },
        "music_band": {
            "vendor_name": "The Sunfolk Acoustic Trio",
            "genre": "Indie folk, acoustic pop covers, ukulele and Cajón beats",
            "includes": ["Acoustic guitar, violin/cello, and percussionist", "Cordless wireless setup for outdoor garden mobility", "Ceremony & reception music"],
            "individual_price_lkr": 190000.0
        },
        "bundle_discount_percent": 10.0
    }
}


def generate_theme_package(theme_name: str) -> Dict[str, Any]:
    """
    Generates a curated vendor fusion package combining a Photographer, Decorator,
    and Music Band matching a wedding theme, with exclusive bundle pricing.

    Parameters:
        theme_name (str): The theme concept (e.g., 'Traditional', 'Vintage', 'Modern Luxury', 'Bohemian', 'Rustic').

    Returns:
        Dict[str, Any]: JSON-serializable dictionary with vendor lineup and discounted package pricing.
    """
    raw_key = (theme_name or "").strip().lower()

    # Match key against preset dictionary
    matched_key = "traditional"  # sensible default
    if "trad" in raw_key or "kandyan" in raw_key or "sinhala" in raw_key:
        matched_key = "traditional"
    elif "vint" in raw_key or "retro" in raw_key or "classic" in raw_key or "ceylon" in raw_key:
        matched_key = "vintage"
    elif "lux" in raw_key or "modern" in raw_key or "glam" in raw_key or "royal" in raw_key:
        matched_key = "modern_luxury"
    elif "boho" in raw_key or "rust" in raw_key or "garden" in raw_key or "beach" in raw_key:
        matched_key = "bohemian_rustic"

    preset = THEME_PRESETS[matched_key]

    photo_price = float(preset["photographer"]["individual_price_lkr"])
    decor_price = float(preset["decorator"]["individual_price_lkr"])
    music_price = float(preset["music_band"]["individual_price_lkr"])

    subtotal = photo_price + decor_price + music_price
    discount_pct = float(preset["bundle_discount_percent"])
    discount_amount = round(subtotal * (discount_pct / 100.0), 2)
    bundle_total = round(subtotal - discount_amount, 2)

    result = {
        "status": "success",
        "theme_requested": theme_name,
        "theme_matched": preset["theme_display_name"],
        "theme_concept": preset["description"],
        "vendor_lineup": {
            "photographer": {
                "role": "Lead Wedding Photographer & Cinematographer",
                "vendor_name": preset["photographer"]["vendor_name"],
                "specialist": preset["photographer"]["lead_specialist"],
                "style": preset["photographer"]["style"],
                "deliverables": preset["photographer"]["includes"],
                "individual_price_lkr": photo_price
            },
            "decorator": {
                "role": "Event Concept Stylist & Floral Designer",
                "vendor_name": preset["decorator"]["vendor_name"],
                "stylist": preset["decorator"]["lead_stylist"],
                "aesthetic_elements": preset["decorator"]["style_elements"],
                "inclusions": preset["decorator"]["includes"],
                "individual_price_lkr": decor_price
            },
            "music_band": {
                "role": "Live Music & Entertainment",
                "vendor_name": preset["music_band"]["vendor_name"],
                "genre": preset["music_band"]["genre"],
                "inclusions": preset["music_band"]["includes"],
                "individual_price_lkr": music_price
            }
        },
        "pricing_summary": {
            "currency": "LKR",
            "combined_individual_total_lkr": float(subtotal),
            "bundle_discount_percentage": float(discount_pct),
            "bundle_savings_lkr": float(discount_amount),
            "total_package_price_lkr": float(bundle_total),
            "booking_terms": "One-click unified booking contract with guaranteed vendor synchronization and zero schedule clashes."
        }
    }

    return convert_decimals(result)
