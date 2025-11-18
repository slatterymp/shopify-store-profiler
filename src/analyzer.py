# src/analyzer.py

import pandas as pd
from collections import Counter
from typing import Dict, Any


def summarize_numeric(series: pd.Series) -> Dict[str, Any]:
    series = pd.to_numeric(series, errors="coerce").dropna()
    if series.empty:
        return {}
    return {
        "count": int(series.count()),
        "min": float(series.min()),
        "max": float(series.max()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std(ddof=0)) if series.count() > 1 else 0.0,
        "p25": float(series.quantile(0.25)),
        "p75": float(series.quantile(0.75)),
    }


def get_tag_counts(df: pd.DataFrame, top_n: int = 30) -> Dict[str, int]:
    all_tags = []
    if "tags_list" in df.columns:
        for tags in df["tags_list"]:
            if isinstance(tags, list):
                all_tags.extend(tags)
    counter = Counter(all_tags)
    return dict(counter.most_common(top_n))


def analyze_products(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Takes the raw products DataFrame and returns a structured profile dict.
    """
    n_products = int(len(df))

    price_stats = summarize_numeric(df.get("first_variant_price"))
    title_len_stats = summarize_numeric(df.get("title_len"))
    desc_len_stats = summarize_numeric(df.get("desc_len"))

    product_type_counts = (
        df.get("product_type", pd.Series(dtype=str))
        .fillna("")
        .replace("", "Unspecified")
        .value_counts()
        .to_dict()
    )

    tag_counts = get_tag_counts(df, top_n=50)

    profile = {
        "n_products": n_products,
        "price_stats": price_stats,
        "title_length_stats": title_len_stats,
        "description_length_stats": desc_len_stats,
        "product_types": product_type_counts,
        "top_tags": tag_counts,
    }

    return profile