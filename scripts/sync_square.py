import os
import sys
import json
import re
import html
import argparse
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HTML_FILE = REPO_ROOT / "index.html"
DATA_FILE = REPO_ROOT / "data" / "treatments.json"

SQUARE_API_URL = "https://connect.squareup.com/v2/catalog/list"
SQUARE_VERSION = "2024-08-21"
BOOKING_URL = "https://square.site/book/LW9BHZQ4T5VW6/glow-and-ember"

STANDARD_CATEGORY_ORDER = ["BROWS", "LASHES", "LIPS", "COMBOS"]

# Curated metadata dictionary for brand badges, subtitles & descriptions
# Used to enrich Square item data when Square only stores title & price
METADATA_FALLBACKS = {
    # Brows
    "Eyebrow Wax": {
        "badge": "Precision Wax",
        "detail": "Gentle Hot Wax Shaping & Tidy",
        "summary": "Clean, tidy, and define your natural brow shape with gentle, skin-friendly hot waxing and a soothing botanical finish.",
        "deposit": 5,
        "featured": False
    },
    "Eyebrow Tint": {
        "badge": "Custom Colour",
        "detail": "Tailored Pigment Depth & Tone",
        "summary": "Custom-blended tint formulated to enrich brow depth, fill lighter hairs, and enhance natural arch fullness.",
        "deposit": 5,
        "featured": False
    },
    "Signature Brows": {
        "badge": "Signature Treatment",
        "detail": "Mapping, Shaping, Wax & Tint",
        "summary": "Our bespoke arch restoration. Includes tailored facial mapping for natural symmetry, custom pigment tinting, precision waxing, and sculpting.",
        "deposit": 15,
        "featured": True
    },
    "Brow Lamination": {
        "badge": "Trending",
        "detail": "Wax, Tint & Sculpt",
        "summary": "Restructures and relaxes brow hairs for a fuller, brushed-up feathered look. Includes precision wax, custom tint, and setting.",
        "deposit": 15,
        "featured": True
    },
    "Hybrid Brows": {
        "badge": "Precision Stain",
        "detail": "Precision Wax, Hybrid Stain & Shape",
        "summary": "Upgrades traditional tinting to a long-lasting hybrid stain for a richer, bolder, makeup-like finish combined with custom mapping and precision wax.",
        "deposit": 15,
        "featured": False
    },
    "Male Brows": {
        "badge": "Men's Grooming",
        "detail": "Subtle Definition & Tidy",
        "summary": "Subtle, natural grooming tailored specifically for male brow structure—maintaining clean, masculine arches without looking over-styled.",
        "deposit": 5,
        "featured": False
    },

    # Eyes
    "Eyelash Tint": {
        "badge": "Lash Enhancement",
        "detail": "Glossy Deep Pigment Tinting",
        "summary": "Deep, glossy lash enhancement that creates the appearance of longer, naturally darker lashes from root to tip without mascara.",
        "deposit": 5,
        "featured": False
    },
    "Lash Lift": {
        "badge": "Root Lift",
        "detail": "Semi-Permanent Curl & Volume",
        "summary": "A gentle semi-permanent treatment that curls and lifts natural lashes from the root, creating an open, wide-awake gaze for weeks.",
        "deposit": 10,
        "featured": False
    },
    "Lash Lift & Tint": {
        "badge": "Root Lift",
        "detail": "Semi-Permanent Lift & Glossy Tint",
        "summary": "Lifts and curls natural lashes from the root while adding a glossy tint for an open, wide-awake gaze that lasts 6-8 weeks.",
        "deposit": 15,
        "featured": True
    },
    "Korean Lash Lift": {
        "badge": "Keratin Infusion",
        "detail": "Gentle Keratin Conditioning & Lift",
        "summary": "An advanced nourishing lift utilizing deeply conditioning keratin solutions to strengthen natural lashes while delivering a soft, elegant curl.",
        "deposit": 15,
        "featured": True
    },
    "Korean Lash Lift & Tint": {
        "badge": "Keratin Infusion",
        "detail": "Nourishing Keratin Lift & Deep Tint",
        "summary": "A modern, gentle keratin treatment that curls, lifts, and nourishes lashes without harsh perming chemicals, finished with deep pigment tinting.",
        "deposit": 15,
        "featured": True
    },

    # Lips & Face
    "Lip Wax": {
        "badge": "Delicate Wax",
        "detail": "Gentle Upper Lip Hair Removal",
        "summary": "Quick, delicate hair removal along the upper lip line for smooth, clear skin using soothing, sensitive hot wax.",
        "deposit": 5,
        "featured": False
    },
    "Lip Waxing": {
        "badge": "Delicate Wax",
        "detail": "Gentle Upper Lip Hair Removal",
        "summary": "Quick, delicate hair removal along the upper lip line for smooth, clear skin using soothing, sensitive hot wax.",
        "deposit": 5,
        "featured": False
    },
    "Chin Wax": {
        "badge": "Delicate Wax",
        "detail": "Gentle Chin Hair Removal",
        "summary": "Smooth, precise hair removal along the chin line using gentle, sensitive hot wax with botanical post-wax care.",
        "deposit": 5,
        "featured": False
    },

    # Combos
    "Signature Brows & Lash Tint": {
        "badge": "Popular Combo",
        "detail": "Signature Brows + Eyelash Tint",
        "summary": "The complete gaze transformation. Pairs our bespoke signature brow mapping, waxing, and tinting with a rich, glossy lash tint for luminous definition and depth.",
        "deposit": 15,
        "featured": True
    },
    "Signature Brows & Eyelash Tint": {
        "badge": "Popular Combo",
        "detail": "Precision Brow Mapping, Tint & Wax + Eyelash Tint",
        "summary": "The complete gaze transformation. Pairs our bespoke signature brow mapping, waxing, and tinting with a rich, glossy lash tint for luminous definition and depth.",
        "deposit": 15,
        "featured": True
    },
    "Signature Brows, Lash Lift & Tint": {
        "badge": "Ultimate Trio",
        "detail": "Signature Brows + Lash Lift & Lash Tint",
        "summary": "Our all-in-one enhancement. Combines precision mapped signature brows with a semi-permanent lash lift and deep tint for effortlessly elevated daily radiance.",
        "deposit": 15,
        "featured": True
    },
    "Brow Lamination & Korean Lash Lift": {
        "badge": "Premier Duo",
        "detail": "Full Brow Lamination + Korean Keratin Lash Lift",
        "summary": "The pinnacle of brow and lash luxury. Combines full brow lamination, waxing, and sculpting with the gentle, deeply nourishing Korean keratin lash lift for maximum fullness and curl.",
        "deposit": 20,
        "featured": True
    },
    "Brow Lamination & Korean Lash Lift & Tint": {
        "badge": "Premier Duo",
        "detail": "Full Brow Lamination + Korean Keratin Lash Lift & Tint",
        "summary": "The pinnacle of brow and lash luxury. Combines full brow lamination, waxing, and sculpting with the gentle, deeply nourishing Korean keratin lash lift and gloss tint.",
        "deposit": 20,
        "featured": True
    },
    "Hybrid Brows & Korean Lash Lift & Tint": {
        "badge": "Ultimate Defined",
        "detail": "Hybrid Stain Brows + Korean Keratin Lash Lift & Tint",
        "summary": "Pairs high-definition hybrid stain brows with a restorative Korean keratin lash lift and deep tint for dramatic, long-lasting definition.",
        "deposit": 20,
        "featured": True
    }
}

ITEM_ORDER = {
    # Brows
    "Eyebrow Wax": 1,
    "Eyebrow Tint": 2,
    "Signature Brows": 3,
    "Brow Lamination": 4,
    "Hybrid Brows": 5,
    "Male Brows": 6,

    # Eyes
    "Eyelash Tint": 1,
    "Lash Lift": 2,
    "Lash Lift & Tint": 2,
    "Korean Lash Lift": 3,
    "Korean Lash Lift & Tint": 3,

    # Lips
    "Lip Wax": 1,
    "Lip Waxing": 1,
    "Chin Wax": 2,

    # Combos
    "Signature Brows & Lash Tint": 1,
    "Signature Brows & Eyelash Tint": 1,
    "Signature Brows, Lash Lift & Tint": 2,
    "Brow Lamination & Korean Lash Lift": 3,
    "Brow Lamination & Korean Lash Lift & Tint": 3,
    "Hybrid Brows & Korean Lash Lift & Tint": 4
}


def classify_category(name: str, square_cat: str) -> str:
    """Uses Square Appointments category directly, with fallback heuristics if uncategorized."""
    if square_cat and square_cat.strip():
        return square_cat.strip()

    # Intelligent fallback heuristics only if category is unassigned in Square
    lower = name.lower()
    if ("brow" in lower and "lash" in lower) or ("lamination" in lower and "lift" in lower) or "combo" in lower:
        return "COMBOS"
    elif "lip" in lower or "chin" in lower:
        return "LIPS"
    elif "lash" in lower or "lift" in lower or "eye" in lower:
        return "LASHES"
    elif "brow" in lower:
        return "BROWS"
    else:
        return "TREATMENTS"



def sanitize_brand_text(text: str) -> str:
    if not text:
        return ""
    pattern = re.compile(r"\brituals?\b", re.IGNORECASE)
    return pattern.sub("treatment", text)


def calculate_deposit(price: int) -> int:
    if price <= 12:
        return 5
    elif price <= 20:
        return 10
    elif price <= 45:
        return 15
    else:
        return 20


def fetch_square_catalog(token: str):
    headers = {
        "Square-Version": SQUARE_VERSION,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    objects = []
    cursor = None

    while True:
        url = f"{SQUARE_API_URL}?types=ITEM,CATEGORY"
        if cursor:
            url += f"&cursor={cursor}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                batch = data.get("objects", [])
                objects.extend(batch)
                cursor = data.get("cursor")
                if not cursor:
                    break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            print(f"[ERROR] Square API returned HTTP {e.code}: {err_body}", file=sys.stderr)
            raise

    return objects


def get_mock_catalog():
    return [
        {"type": "CATEGORY", "id": "cat_brows", "category_data": {"name": "BROWS"}},
        {"type": "CATEGORY", "id": "cat_lashes", "category_data": {"name": "LASHES"}},
        {"type": "CATEGORY", "id": "cat_lips", "category_data": {"name": "LIPS"}},
        {"type": "CATEGORY", "id": "cat_combos", "category_data": {"name": "COMBOS"}},
        # Brows
        {"type": "ITEM", "id": "item_1", "item_data": {
            "name": "Eyebrow Wax", "category_id": "cat_brows",
            "variations": [{"item_variation_data": {"price_money": {"amount": 1000}, "service_duration": 1800000}}]
        }},
        {"type": "ITEM", "id": "item_2", "item_data": {
            "name": "Eyebrow Tint", "category_id": "cat_brows",
            "variations": [{"item_variation_data": {"price_money": {"amount": 1000}, "service_duration": 1800000}}]
        }},
        {"type": "ITEM", "id": "item_3", "item_data": {
            "name": "Signature Brows", "category_id": "cat_brows",
            "description": "Mapping, Shaping, Wax & Tint",
            "variations": [{"item_variation_data": {"price_money": {"amount": 2500}, "service_duration": 2700000}}]
        }},
        {"type": "ITEM", "id": "item_4", "item_data": {
            "name": "Brow Lamination", "category_id": "cat_brows",
            "description": "Wax, Tint & Sculpt",
            "variations": [{"item_variation_data": {"price_money": {"amount": 3500}, "service_duration": 3600000}}]
        }},
        {"type": "ITEM", "id": "item_5", "item_data": {
            "name": "Hybrid Brows", "category_id": "cat_brows",
            "description": "Precision Wax, Tint & Shape",
            "variations": [{"item_variation_data": {"price_money": {"amount": 2800}, "service_duration": 3600000}}]
        }},
        # Lashes / Eyes
        {"type": "ITEM", "id": "item_6", "item_data": {
            "name": "Eyelash Tint", "category_id": "cat_lashes",
            "variations": [{"item_variation_data": {"price_money": {"amount": 1500}, "service_duration": 1800000}}]
        }},
        {"type": "ITEM", "id": "item_7", "item_data": {
            "name": "Lash Lift & Tint", "category_id": "cat_lashes",
            "variations": [{"item_variation_data": {"price_money": {"amount": 3000}, "service_duration": 2700000}}]
        }},
        {"type": "ITEM", "id": "item_8", "item_data": {
            "name": "Korean Lash Lift & Tint", "category_id": "cat_lashes",
            "variations": [{"item_variation_data": {"price_money": {"amount": 4500}, "service_duration": 5400000}}]
        }},
        # Combos
        {"type": "ITEM", "id": "item_9", "item_data": {
            "name": "Signature Brows, Lash Lift & Tint", "category_id": "cat_combos",
            "description": "Signature Brows + Lash Lift & Lash Tint",
            "variations": [{"item_variation_data": {"price_money": {"amount": 5000}, "service_duration": 5400000}}]
        }},
        {"type": "ITEM", "id": "item_10", "item_data": {
            "name": "Brow Lamination & Korean Lash Lift & Tint", "category_id": "cat_combos",
            "variations": [{"item_variation_data": {"price_money": {"amount": 7500}, "service_duration": 6300000}}]
        }},
        {"type": "ITEM", "id": "item_11", "item_data": {
            "name": "Hybrid Brows & Korean Lash Lift & Tint", "category_id": "cat_combos",
            "variations": [{"item_variation_data": {"price_money": {"amount": 7000}, "service_duration": 6300000}}]
        }},
        # Lips
        {"type": "ITEM", "id": "item_12", "item_data": {
            "name": "Lip Wax", "category_id": "cat_lips",
            "variations": [{"item_variation_data": {"price_money": {"amount": 500}, "service_duration": 900000}}]
        }},
        {"type": "ITEM", "id": "item_13", "item_data": {
            "name": "Chin Wax", "category_id": "cat_lips",
            "variations": [{"item_variation_data": {"price_money": {"amount": 500}, "service_duration": 900000}}]
        }}
    ]


def parse_catalog(catalog_objects):
    categories = {}
    items_by_cat = {}

    for obj in catalog_objects:
        if obj.get("is_deleted"):
            continue
        if obj.get("type") == "CATEGORY":
            cat_data = obj.get("category_data", {})
            name = sanitize_brand_text(cat_data.get("name", "").strip())
            categories[obj["id"]] = name

    for obj in catalog_objects:
        if obj.get("is_deleted"):
            continue
        if obj.get("type") == "ITEM":
            item_data = obj.get("item_data", {})

            # Filter out archived items
            if item_data.get("is_archived"):
                continue

            # Check variations: filter out deleted or unbookable variations
            variations = item_data.get("variations", [])
            active_vars = []
            for v in variations:
                if v.get("is_deleted"):
                    continue
                v_data = v.get("item_variation_data") or {}
                if v_data.get("available_for_booking") is False:
                    continue
                active_vars.append(v)

            # If item has variations but none are active for booking, skip item
            if variations and not active_vars:
                continue

            cat_id = item_data.get("category_id")
            square_cat = categories.get(cat_id, "")

            raw_name = item_data.get("name", "").strip()
            name = sanitize_brand_text(raw_name)
            lower_name = name.lower()

            # Skip patch test from main service grid (already in dedicated spotlight section)
            if "patch test" in lower_name:
                continue

            active_var = active_vars[0] if active_vars else (variations[0] if variations else {})
            var_data = active_var.get("item_variation_data") or {}
            price_money = var_data.get("price_money") or {}
            price_amount = price_money.get("amount", 0) or 0
            price = int(price_amount // 100)
            duration_ms = var_data.get("service_duration") or 1800000
            duration_mins = int(duration_ms // 60000)

            # Filter out discontinued student items
            if "student" in lower_name:
                continue

            target_cat = classify_category(name, square_cat)
            fallback = METADATA_FALLBACKS.get(name, {})
            sq_desc = sanitize_brand_text(item_data.get("description", "").strip())

            # Intelligent subtitle and description resolution:
            # If Square has a short subtitle-like description (e.g. "Wax, Tint & Sculpt"), use as detail
            if sq_desc and len(sq_desc) <= 65:
                detail = sq_desc
                summary = fallback.get("summary") or sq_desc
            elif sq_desc:
                summary = sq_desc
                detail = fallback.get("detail", f"{duration_mins} mins tailored treatment")
            else:
                detail = fallback.get("detail", f"{duration_mins} mins tailored treatment")
                summary = fallback.get("summary", "Bespoke beauty treatment tailored to your natural features.")

            badge = fallback.get("badge", "Essential")
            deposit = fallback.get("deposit", calculate_deposit(price))
            featured = fallback.get("featured", ("Signature" in name or "Lamination" in name or target_cat.upper() == "COMBOS"))

            treatment = {
                "name": name,
                "price": price,
                "duration": duration_mins,
                "badge": badge,
                "detail": detail,
                "summary": summary,
                "deposit": deposit,
                "featured": featured
            }

            items_by_cat.setdefault(target_cat, []).append(treatment)

    # Sort treatments within each category according to physical menu order
    for cat in items_by_cat:
        items_by_cat[cat].sort(key=lambda t: ITEM_ORDER.get(t["name"], 99))

    print(f"[INFO] Parsed {sum(len(v) for v in items_by_cat.values())} treatments across {len(items_by_cat)} categories:")
    for cat, items in items_by_cat.items():
        print(f"  [{cat}] ({len(items)} treatments)")
        for t in items:
            print(f"    • {t['name']} — £{t['price']} ({t['duration']} mins)")

    return items_by_cat


def sort_categories(cat_names):
    def sort_key(name):
        norm = name.strip().upper()
        if norm in STANDARD_CATEGORY_ORDER:
            return (0, STANDARD_CATEGORY_ORDER.index(norm))
        return (1, norm)
    return sorted(cat_names, key=sort_key)


def generate_html_cards(items_by_cat) -> str:
    ordered_cats = sort_categories(items_by_cat.keys())
    lines = []

    for idx, cat_name in enumerate(ordered_cats, start=1):
        items = items_by_cat[cat_name]
        cat_slug = re.sub(r'[^a-z0-9]+', '-', cat_name.lower()).strip('-')
        is_single = (len(items) == 1)

        lines.append(f'      <!-- GROUP {idx}: {cat_name.upper()} -->')
        lines.append(f'      <div class="treatment-group" id="group-{cat_slug}">')
        lines.append('        <div class="menu-category-header">')
        lines.append('          <span class="category-rule"></span>')
        lines.append(f'          <h3 class="category-title">{html.escape(cat_name, quote=False)}</h3>')
        lines.append('          <span class="category-rule right"></span>')
        lines.append('        </div>')
        lines.append('')

        grid_class = "single-card-wrap" if is_single else "category-cards-grid"
        lines.append(f'        <div class="{grid_class}">')

        for item in items:
            card_class = "treatment-card featured-card" if item["featured"] else "treatment-card"
            badge_class = "treatment-badge featured" if item["featured"] else "treatment-badge"
            name_escaped = html.escape(item["name"], quote=False)
            badge_escaped = html.escape(item["badge"], quote=False)
            detail_escaped = html.escape(item["detail"], quote=False)
            summary_escaped = html.escape(item["summary"], quote=False)

            lines.append(f'          <!-- {item["name"]} -->')
            lines.append(f'          <article class="{card_class}">')
            lines.append('            <div class="card-head">')
            lines.append('              <div class="card-top">')
            lines.append(f'                <span class="{badge_class}">{badge_escaped}</span>')
            lines.append('                <div class="price-lockup">')
            lines.append(f'                  <span class="price">&pound;{item["price"]}</span>')
            lines.append(f'                  <span class="duration">{item["duration"]} mins</span>')
            lines.append('                </div>')
            lines.append('              </div>')
            lines.append(f'              <h4 class="treatment-name">{name_escaped}</h4>')
            lines.append(f'              <p class="treatment-detail">{detail_escaped}</p>')
            lines.append('            </div>')
            lines.append('            <p class="treatment-summary">')
            lines.append(f'              {summary_escaped}')
            lines.append('            </p>')
            lines.append('            <div class="card-footer">')
            lines.append(f'              <span class="deposit-note">Deposit: &pound;{item["deposit"]}</span>')
            lines.append('              <a ')
            lines.append(f'                href="{BOOKING_URL}" ')
            lines.append('                class="card-book-btn" ')
            lines.append('                target="_blank" ')
            lines.append('                rel="noopener noreferrer"')
            lines.append('              >')
            lines.append('                <span>Book</span>')
            lines.append('                <span class="arrow">&rarr;</span>')
            lines.append('              </a>')
            lines.append('            </div>')
            lines.append('          </article>')
            lines.append('')

        lines.append('        </div>')
        lines.append('      </div>')
        lines.append('')

    return "\n".join(lines).rstrip()


def inject_into_html(html_path: Path, new_menu_html: str):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r'(<!--\s*SQUARE_MENU_START\s*-->).*?(<!--\s*SQUARE_MENU_END\s*-->)',
        re.DOTALL
    )

    if not pattern.search(content):
        raise ValueError(
            "Markers <!-- SQUARE_MENU_START --> and <!-- SQUARE_MENU_END --> "
            "not found in target HTML file."
        )

    replacement = r'\1' + '\n' + new_menu_html + '\n      ' + r'\2'
    updated_content = pattern.sub(replacement, content)

    # Bump CSS cache buster
    updated_content = re.sub(
        r'assets/css/style\.css\?v=(\d+)',
        lambda m: f"assets/css/style.css?v={int(m.group(1)) + 1}",
        updated_content
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"[OK] Successfully updated menu in {html_path}")


def main():
    parser = argparse.ArgumentParser(description="Synchronize Square Catalog with Glow & Ember website.")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing files.")
    parser.add_argument("--mock", action="store_true", help="Use built-in mock catalog data instead of calling Square.")
    parser.add_argument("--token", default=os.environ.get("SQUARE_ACCESS_TOKEN"), help="Square Access Token.")
    args = parser.parse_args()

    if args.mock:
        print("[INFO] Running in MOCK mode (using verified local catalog).")
        raw_objects = get_mock_catalog()
    elif args.token:
        print("[INFO] Connecting to Square Catalog API...")
        try:
            raw_objects = fetch_square_catalog(args.token)
            print(f"[INFO] Fetched {len(raw_objects)} catalog objects from Square.")
        except Exception as e:
            print(f"[ERROR] Failed to fetch Square Catalog: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("[WARN] No SQUARE_ACCESS_TOKEN provided and --mock flag not passed.")
        print("[INFO] Defaulting to MOCK mode for dry-run verification.")
        raw_objects = get_mock_catalog()

    items_by_cat = parse_catalog(raw_objects)
    html_markup = generate_html_cards(items_by_cat)

    if args.dry_run:
        print("\n--- GENERATED HTML PREVIEW ---\n")
        print(html_markup[:800] + "\n... [truncated] ...\n")
        print(f"[INFO] Dry run complete. {sum(len(v) for v in items_by_cat.values())} treatments parsed.")
        return

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items_by_cat, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved catalog audit cache to {DATA_FILE}")

    inject_into_html(HTML_FILE, html_markup)


if __name__ == "__main__":
    main()
