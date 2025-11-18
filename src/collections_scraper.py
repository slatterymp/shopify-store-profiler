# src/collections_scraper.py

import requests
import pandas as pd
from typing import Dict, Any, Tuple

from .shopify_scraper import normalize_store_url, ShopifyScraperError


def fetch_collections(store_url: str, limit: int = 250) -> pd.DataFrame:
    """
    Fetch public collections from /collections.json.

    Returns a pandas DataFrame with one row per collection.

    Some stores may:
      - block this endpoint
      - return 404
      - return an empty list

    In those cases, raises ShopifyScraperError.
    """
    base_url = normalize_store_url(store_url)
    collections = []
    page = 1

    while True:
        url = f"{base_url}/collections.json?limit={limit}&page={page}"
        resp = requests.get(url, timeout=10)

        # 404 or 401 etc → treat as "no collections available"
        if resp.status_code == 404:
            raise ShopifyScraperError("collections.json not available (404)")
        if resp.status_code == 401 or resp.status_code == 403:
            raise ShopifyScraperError("collections.json is not publicly accessible")
        if resp.status_code != 200:
            raise ShopifyScraperError(
                f"Failed fetching {url} (status {resp.status_code})"
            )

        data = resp.json()
        batch = data.get("collections", [])
        if not batch:
            break

        collections.extend(batch)
        if len(batch) < limit:
            break

        page += 1

    if not collections:
        raise ShopifyScraperError("No collections returned from collections.json")

    df = pd.json_normalize(collections)

    # Normalize some fields that are often useful
    # Common fields: id, handle, title, body_html, sort_order, template_suffix,
    # published_at, updated_at, rules, disjunctive, products_count (sometimes)
    if "title" not in df.columns:
        df["title"] = ""
    if "handle" not in df.columns:
        df["handle"] = ""

    # products_count isn't guaranteed, but when it exists it's gold
    if "products_count" in df.columns:
        df["products_count"] = pd.to_numeric(df["products_count"], errors="coerce")
    else:
        df["products_count"] = pd.NA

    return df


def summarize_collections(df: pd.DataFrame, top_n: int = 20) -> Dict[str, Any]:
    """
    Produce a lightweight summary of collections.
    """
    n_collections = int(len(df))

    # how many have non-null product counts
    if "products_count" in df.columns:
        has_counts = df["products_count"].notna().sum()
    else:
        has_counts = 0

    # top collections by products_count, where available
    top_by_products = []
    if "products_count" in df.columns:
        tmp = (
            df[["title", "handle", "products_count"]]
            .copy()
        )
        tmp["products_count"] = pd.to_numeric(tmp["products_count"], errors="coerce")
        tmp = tmp.dropna(subset=["products_count"])
        tmp = tmp.sort_values("products_count", ascending=False).head(top_n)

        for _, row in tmp.iterrows():
            top_by_products.append(
                {
                    "title": str(row.get("title", "")),
                    "handle": str(row.get("handle", "")),
                    "products_count": int(row["products_count"]),
                }
            )

    # crude type breakdown, if template_suffix or rules exist
    template_counts = {}
    if "template_suffix" in df.columns:
        template_counts = (
            df["template_suffix"]
            .fillna("")
            .replace("", "default")
            .value_counts()
            .to_dict()
        )

    summary: Dict[str, Any] = {
        "n_collections": n_collections,
        "collections_with_product_counts": int(has_counts),
        "top_collections_by_products": top_by_products,
        "template_suffix_counts": template_counts,
    }

    return summary