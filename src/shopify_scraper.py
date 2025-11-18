# src/shopify_scraper.py

import requests
import pandas as pd
from urllib.parse import urlparse


class ShopifyScraperError(Exception):
    pass


def normalize_store_url(store_url: str) -> str:
    store_url = store_url.strip()
    if not store_url.startswith("http://") and not store_url.startswith("https://"):
        store_url = "https://" + store_url
    # strip path, keep scheme + netloc
    parsed = urlparse(store_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    return base


def fetch_products(store_url: str, limit: int = 250) -> pd.DataFrame:
    """
    Fetch all public products from a Shopify store's /products.json endpoint.
    Returns a pandas DataFrame with one row per product.
    """
    base_url = normalize_store_url(store_url)
    products = []
    page = 1

    while True:
        url = f"{base_url}/products.json?limit={limit}&page={page}"
        resp = requests.get(url, timeout=10)

        if resp.status_code != 200:
            raise ShopifyScraperError(
                f"Failed fetching {url} (status {resp.status_code})"
            )

        data = resp.json()
        batch = data.get("products", [])
        if not batch:
            break

        products.extend(batch)
        if len(batch) < limit:
            break

        page += 1

    if not products:
        raise ShopifyScraperError("No products found. Store may be empty or locked.")

    df = pd.json_normalize(products)

    # First variant price
    if "variants" in df.columns:
        df["first_variant_price"] = df["variants"].apply(
            lambda vs: float(vs[0].get("price")) if isinstance(vs, list) and vs else None
        )
    else:
        df["first_variant_price"] = None

    # Title / description lengths
    df["title"] = df.get("title", "")
    df["body_html"] = df.get("body_html", "")

    df["title_len"] = df["title"].astype(str).str.len()
    df["desc_len"] = df["body_html"].astype(str).str.len()

    # Tags normalization
    def normalize_tags(x):
        if isinstance(x, list):
            return [str(t).strip() for t in x if str(t).strip()]
        if pd.isna(x):
            return []
        return [t.strip() for t in str(x).split(",") if t.strip()]

    df["tags_list"] = df.get("tags", "").apply(normalize_tags)

    # Product type
    df["product_type"] = df.get("product_type", "").fillna("")

    return df
