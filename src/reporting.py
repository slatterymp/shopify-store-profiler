# src/reporting.py

import os
import json
import pandas as pd
from urllib.parse import urlparse
from typing import Dict, Any

from .shopify_scraper import fetch_products, normalize_store_url, ShopifyScraperError
from .analyzer import analyze_products
from .visuals import generate_figures
from .collections_scraper import fetch_collections, summarize_collections
from .sitemap_scraper import fetch_sitemap_urls, summarize_sitemap
from .tech_stack import fetch_homepage_html, detect_tech_stack
from .product_clustering import cluster_products, ProductClusteringError



def store_slug_from_url(store_url: str) -> str:
    base = normalize_store_url(store_url)
    parsed = urlparse(base)
    return parsed.netloc.replace(".", "_")


def ensure_store_dirs(base_dir: str, store_slug: str) -> dict:
    root = os.path.join(base_dir, store_slug)
    os.makedirs(root, exist_ok=True)
    figs = os.path.join(root, "figures")
    os.makedirs(figs, exist_ok=True)
    return {"root": root, "figures": figs}


def _write_markdown_report(
    profile: Dict[str, Any],
    out_path: str,
):
    store_url = profile.get("store_url", "")
    slug = profile.get("store_slug", "")
    collections_summary = profile.get("collections", {})
    n_products = profile.get("n_products", 0)
    price_stats = profile.get("price_stats", {})
    product_types = profile.get("product_types", {})
    top_tags = profile.get("top_tags", {})
    collections_summary = profile.get("collections", {})
    sitemap_summary = profile.get("sitemap", {})
    tech_stack = profile.get("tech_stack", {})
    clustering = profile.get("clustering", {})

    lines = []

    lines.append(f"# Store profile: {store_url}")
    lines.append("")
    lines.append(f"- Store slug: `{slug}`")
    lines.append(f"- Total products (from /products.json): **{n_products}**")
    lines.append("")

    # Price overview
    if price_stats:
        lines.append("## Price overview")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        for key in ["min", "max", "mean", "median", "p25", "p75"]:
            if key in price_stats:
                val = price_stats[key]
                try:
                    val_str = f"{val:.2f}"
                except TypeError:
                    val_str = str(val)
                lines.append(f"| {key} | {val_str} |")
        lines.append("")

    # Product types
    if product_types:
        lines.append("## Top product types")
        lines.append("")
        lines.append("| Product type | Count |")
        lines.append("|--------------|-------|")
        for pt, count in list(product_types.items())[:20]:
            lines.append(f"| {pt} | {count} |")
        lines.append("")

    # Collections section
    if collections_summary:
        lines.append("## Collections overview")
        lines.append("")
        n_col = collections_summary.get("n_collections", 0)
        n_with_counts = collections_summary.get(
            "collections_with_product_counts", 0
        )
        lines.append(f"- Total collections (from `/collections.json`): **{n_col}**")
        lines.append(
            f"- Collections with explicit `products_count`: **{n_with_counts}**"
        )
        lines.append("")

        # Top collections by products_count
        top_cols = collections_summary.get("top_collections_by_products", [])
        if top_cols:
            lines.append("### Top collections by product count")
            lines.append("")
            lines.append("| Title | Handle | Products |")
            lines.append("|-------|--------|----------|")
            for c in top_cols[:20]:
                title = c.get("title", "")
                handle = c.get("handle", "")
                products_count = c.get("products_count", "")
                lines.append(f"| {title} | `{handle}` | {products_count} |")
            lines.append("")

        # Template suffix breakdown
        template_counts = collections_summary.get("template_suffix_counts", {})
        if template_counts:
            lines.append("### Collection templates")
            lines.append("")
            lines.append("| Template suffix | Count |")
            lines.append("|-----------------|-------|")
            for tpl, count in template_counts.items():
                lines.append(f"| `{tpl}` | {count} |")
            lines.append("")

        # Sitemap / SEO footprint
    if sitemap_summary:
        lines.append("## Sitemap / SEO footprint")
        lines.append("")
        total_urls = sitemap_summary.get("total_urls", 0)
        by_type = sitemap_summary.get("by_type", {})
        latest_lastmod = sitemap_summary.get("latest_lastmod", None)

        lines.append(f"- Total URLs in sitemap: **{total_urls}**")
        if latest_lastmod:
            lines.append(f"- Latest `lastmod`: `{latest_lastmod}`")
        lines.append("")

        if by_type:
            lines.append("### URLs by type")
            lines.append("")
            lines.append("| Type | Count |")
            lines.append("|------|-------|")
            for t, count in by_type.items():
                lines.append(f"| {t} | {count} |")
            lines.append("")

        example_urls = sitemap_summary.get("example_urls", {})
        if example_urls:
            lines.append("### Example URLs by type")
            lines.append("")
            for t, urls in example_urls.items():
                lines.append(f"**{t}**")
                lines.append("")
                for u in urls:
                    lines.append(f"- {u}")
                lines.append("")

    # Tech stack
    if tech_stack:
        lines.append("## Tech stack (heuristic)")
        lines.append("")

        theme_hint = tech_stack.get("theme_hint")
        apps = tech_stack.get("apps_detected", [])
        pixels = tech_stack.get("pixels", {})

        if theme_hint:
            lines.append(f"- Theme hint: **{theme_hint}**")
        lines.append("")

        if apps:
            lines.append("### Detected apps")
            lines.append("")
            for app in apps:
                lines.append(f"- {app}")
            lines.append("")

        if pixels:
            lines.append("### Tracking / pixels")
            lines.append("")
            lines.append("| Tool | Detected |")
            lines.append("|------|----------|")
            for name, present in pixels.items():
                lines.append(f"| {name} | {'yes' if present else 'no'} |")
            lines.append("")

    # Clustering
    if clustering and clustering.get("clusters"):
        lines.append("## Product clustering (heuristic)")
        lines.append("")
        n_clusters = clustering.get("n_clusters", 0)
        lines.append(f"- Number of clusters: **{n_clusters}**")
        lines.append("")

        lines.append("| Cluster | Size | Avg price | Top product types | Example titles |")
        lines.append("|---------|------|-----------|-------------------|----------------|")

        for c in clustering.get("clusters", []):
            cid = c.get("cluster_id")
            size = c.get("size", 0)
            avg_price = c.get("avg_price", None)
            if avg_price is None:
                avg_price_str = ""
            else:
                try:
                    avg_price_str = f"{avg_price:.2f}"
                except TypeError:
                    avg_price_str = str(avg_price)

            top_types = c.get("top_product_types", {})
            top_types_str = ", ".join(
                [f"{k} ({v})" for k, v in top_types.items()]
            )

            example_titles = c.get("example_titles", [])
            # truncate titles a bit so the table doesn't become cursed
            example_titles_str = "; ".join(
                [t[:40] + ("…" if len(t) > 40 else "") for t in example_titles]
            )

            lines.append(
                f"| C{cid} | {size} | {avg_price_str} | {top_types_str} | {example_titles_str} |"
            )

        lines.append("")

    # Tags
    if top_tags:
        lines.append("## Top tags")
        lines.append("")
        lines.append("| Tag | Count |")
        lines.append("|-----|-------|")
        for tag, count in list(top_tags.items())[:30]:
            lines.append(f"| `{tag}` | {count} |")
        lines.append("")

    content = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_store_report(store_url: str, data_dir: str = "data") -> dict:
    """
    High-level pipeline:
      1. Fetch products into DataFrame
      2. Analyze products
      3. Optionally fetch/summarize collections
      4. Save raw + summary artifacts to /data/<store>/
      5. Generate figures and markdown report
      6. Return the profile dict
    """
    store_url = normalize_store_url(store_url)
    slug = store_slug_from_url(store_url)
    dirs = ensure_store_dirs(data_dir, slug)

    # 1) scrape products
    df_products = fetch_products(store_url)

    # 2) analyze products
    profile = analyze_products(df_products)
    profile["store_url"] = store_url
    profile["store_slug"] = slug

        # 2b) product clustering (optional, heuristic)
    try:
        df_products, clustering_summary = cluster_products(df_products)
        profile["clustering"] = clustering_summary
    except ProductClusteringError:
        profile["clustering"] = {}
    except Exception:
        profile["clustering"] = {}


    # 3) try collections.json
    collections_df: pd.DataFrame | None = None
    collections_summary: Dict[str, Any] | None = None
    try:
        collections_df = fetch_collections(store_url)
        collections_summary = summarize_collections(collections_df)
        profile["collections"] = collections_summary
    except ShopifyScraperError:
        # Collections not available / blocked / empty; just skip silently
        profile["collections"] = {}
    except Exception:
        # Anything unexpected: don't crash the whole report
        profile["collections"] = {}

        # 3b) try sitemap.xml
    try:
        sitemap_urls = fetch_sitemap_urls(store_url)
        sitemap_summary = summarize_sitemap(sitemap_urls)
        profile["sitemap"] = sitemap_summary
    except ShopifyScraperError:
        profile["sitemap"] = {}
    except Exception:
        profile["sitemap"] = {}

            # 3c) try homepage tech stack detection
    try:
        homepage_html = fetch_homepage_html(store_url)
        tech = detect_tech_stack(homepage_html)
        profile["tech_stack"] = tech

        # Optional: save HTML snapshot for inspection
        html_path = os.path.join(dirs["root"], "homepage.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(homepage_html)
    except ShopifyScraperError:
        profile["tech_stack"] = {}
    except Exception:
        profile["tech_stack"] = {}


    # 4) save artifacts
    # products
    products_path = os.path.join(dirs["root"], "products.parquet")
    df_products.to_parquet(products_path, index=False)

    products_csv_path = os.path.join(dirs["root"], "products_summary.csv")
    cols = [
        "id",
        "title",
        "handle",
        "first_variant_price",
        "product_type",
        "tags_list",
        "title_len",
        "desc_len",
        "cluster",
    ]
    cols = [c for c in cols if c in df_products.columns]
    df_products[cols].to_csv(products_csv_path, index=False)

    # collections, if we have them
    if collections_df is not None:
        collections_parquet_path = os.path.join(dirs["root"], "collections.parquet")
        collections_df.to_parquet(collections_parquet_path, index=False)

        # small CSV with just key fields
        c_cols = ["id", "title", "handle", "products_count"]
        c_cols = [c for c in c_cols if c in collections_df.columns]
        if c_cols:
            collections_csv_path = os.path.join(
                dirs["root"], "collections_summary.csv"
            )
            collections_df[c_cols].to_csv(collections_csv_path, index=False)

    # summary JSON
    summary_path = os.path.join(dirs["root"], "profile.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    # 5) figures (based on products)
    generate_figures(df_products, profile, dirs["figures"])

    # 6) markdown report
    md_path = os.path.join(dirs["root"], "report.md")
    _write_markdown_report(profile, md_path)

    return profile