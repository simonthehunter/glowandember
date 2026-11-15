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

CATEGORY_ORDER = ["Brows", "Eyes", "Lips", "Combos"]

# Curated metadata dictionary for brand badges, subtitles & descriptions
# Used to enrich Square item data when Square only stores title & price
METADATA_FALLBACKS = {
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
    "Male Brows": {
        "badge": "Men's Grooming",
        "detail": "Subtle Definition & Tidy",
        "summary": "Subtle, natural grooming tailored specifically for male brow structure—maintaining clean, masculine arches without looking over-styled.",
        "deposit": 5,
        "featured": False
    },
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
    "Korean Lash Lift": {
        "badge": "Keratin Infusion",
        "detail": "Gentle Keratin Conditioning & Lift",
        "summary": "An advanced nourishing lift utilizing deeply conditioning keratin solutions to strengthen natural lashes while delivering a soft, elegant curl.",
        "deposit": 15,
        "featured": True
    },
    "Lip Waxing": {
        "badge": "Delicate Wax",
        "detail": "Gentle Upper Lip Hair Removal",
        "summary": "Quick, delicate hair removal along the upper lip line for smooth, clear skin using soothing, sensitive hot wax.",
        "deposit": 5,
        "featured": False
    },
    "Signature Brows & Lash Tint": {
        "badge": "Popular Combo",
        "detail": "Signature Brows + Eyelash Tint",
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
    }
}


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
        {"type": "CATEGORY", "id": "cat_brows", "category_data": {"name": "Brows"}},
        {"type": "CATEGORY", "id": "cat_eyes", "category_data": {"name": "Eyes"}},
        {"type": "CATEGORY", "id": "cat_lips", "category_data": {"name": "Lips"}},
        {"type": "CATEGORY", "id": "cat_combos", "category_data": {"name": "Combos"}},
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
            "variations": [{"item_variation_data": {"price_money": {"amount": 2500}, "service_duration": 2700000}}]
        }},
        {"type": "ITEM", "id": "item_4", "item_data": {
            "name": "Brow Lamination", "category_id": "cat_brows",
            "variations": [{"item_variation_data": {"price_money": {"amount": 3000}, "service_duration": 2700000}}]
        }},
        {"type": "ITEM", "id": "item_5", "item_data": {
            "name": "Male Brows", "category_id": "cat_brows",
            "variations": [{"item_variation_data": {"price_money": {"amount": 1200}, "service_duration": 1800000}}]
        }},
        {"type": "ITEM", "id": "item_6", "item_data": {
            "name": "Eyelash Tint", "category_id": "cat_eyes",
            "variations": [{"item_variation_data": {"price_money": {"amount": 1000}, "service_duration": 1800000}}]
        }},
        {"type": "ITEM", "id": "item_7", "item_data": {
            "name": "Lash Lift", "category_id": "cat_eyes",
            "variations": [{"item_variation_data": {"price_money": {"amount": 2000}, "service_duration": 2700000}}]
        }},
        {"type": "ITEM", "id": "item_8", "item_data": {
            "name": "Korean Lash Lift", "category_id": "cat_eyes",
            "variations": [{"item_variation_data": {"price_money": {"amount": 4000}, "service_duration": 3000000}}]
        }},
        {"type": "ITEM", "id": "item_9", "item_data": {
            "name": "Lip Waxing", "category_id": "cat_lips",
            "variations": [{"item_variation_data": {"price_money": {"amount": 800}, "service_duration": 900000}}]
        }},
        {"type": "ITEM", "id": "item_10", "item_data": {
            "name": "Signature Brows & Lash Tint", "category_id": "cat_combos",
            "variations": [{"item_variation_data": {"price_money": {"amount": 3000}, "service_duration": 3300000}}]
        }},
        {"type": "ITEM", "id": "item_11", "item_data": {
            "name": "Signature Brows, Lash Lift & Tint", "category_id": "cat_combos",
            "variations": [{"item_variation_data": {"price_money": {"amount": 4500}, "service_duration": 3900000}}]
        }},
        {"type": "ITEM", "id": "item_12", "item_data": {
            "name": "Brow Lamination & Korean Lash Lift", "category_id": "cat_combos",
            "variations": [{"item_variation_data": {"price_money": {"amount": 6500}, "service_duration": 4500000}}]
        }}
    ]


def parse_catalog(catalog_objects):
    categories = {}
    items_by_cat = {}

    for obj in catalog_objects:
        if obj.get("type") == "CATEGORY":
            cat_data = obj.get("category_data", {})
            name = sanitize_brand_text(cat_data.get("name", "").strip())
            categories[obj["id"]] = name

    for obj in catalog_objects:
        if obj.get("type") == "ITEM":
            item_data = obj.get("item_data", {})
            cat_id = item_data.get("category_id")
            cat_name = categories.get(cat_id, "Treatments")
            
            raw_name = item_data.get("name", "").strip()
            name = sanitize_brand_text(raw_name)
            
            if name.lower() == "signature brows & lash tint":
                name = "Signature Brows & Lash Tint"

            variations = item_data.get("variations", [])
            price = 0
            duration_mins = 30
            if variations:
                var_data = variations[0].get("item_variation_data", {})
                price_amount = var_data.get("price_money", {}).get("amount", 0)
                price = int(price_amount // 100)
                duration_ms = var_data.get("service_duration", 1800000)
                duration_mins = int(duration_ms // 60000)

            fallback = METADATA_FALLBACKS.get(name, {})
            sq_desc = sanitize_brand_text(item_data.get("description", "").strip())
            
            badge = fallback.get("badge", "Essential")
            detail = fallback.get("detail", f"{duration_mins} mins tailored treatment")
            summary = sq_desc if sq_desc else fallback.get("summary", "Bespoke beauty treatment tailored to your natural features.")
            deposit = fallback.get("deposit", calculate_deposit(price))
            featured = fallback.get("featured", ("Signature" in name or "Lamination" in name or cat_name == "Combos"))

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

            items_by_cat.setdefault(cat_name, []).append(treatment)

    return items_by_cat


def generate_html_cards(items_by_cat) -> str:
    ordered_cats = []
    for cat in CATEGORY_ORDER:
        if cat in items_by_cat:
            ordered_cats.append(cat)
    for cat in sorted(items_by_cat.keys()):
        if cat not in ordered_cats:
            ordered_cats.append(cat)

    lines = []

    for idx, cat_name in enumerate(ordered_cats, start=1):
        items = items_by_cat[cat_name]
        cat_slug = cat_name.lower().replace(" ", "-")
        is_single = (len(items) == 1)

        lines.append(f'      <!-- GROUP {idx}: {cat_name.upper()} -->')
        lines.append(f'      <div class="treatment-group" id="group-{cat_slug}">')
        lines.append('        <div class="menu-category-header">')
        lines.append('          <span class="category-rule"></span>')
        lines.append(f'          <h3 class="category-title">{cat_name}</h3>')
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
