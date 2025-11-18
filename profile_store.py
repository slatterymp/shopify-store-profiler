# profile_store.py

# profile_store.py

import sys
import json

from src.reporting import generate_store_report  # this is the key


def main():
    if len(sys.argv) < 2:
        print("Usage: python profile_store.py <shopify_store_url>")
        sys.exit(1)

    store_url = sys.argv[1].strip()

    try:
        profile = generate_store_report(store_url)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # Pretty-print a short summary to stdout
    summary = {
        "store_url": profile.get("store_url"),
        "n_products": profile.get("n_products"),
        "price_stats": profile.get("price_stats"),
        "top_product_types": dict(list(profile.get("product_types", {}).items())[:5]),
        "top_tags": dict(list(profile.get("top_tags", {}).items())[:10]),
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()