# src/sitemap_scraper.py

import requests
from urllib.parse import urlparse
from typing import Dict, Any, List, Tuple, Optional
import xml.etree.ElementTree as ET

from .shopify_scraper import normalize_store_url, ShopifyScraperError


def _fetch_xml(url: str, timeout: int = 10) -> Optional[ET.Element]:
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        return None
    try:
        root = ET.fromstring(resp.content)
        return root
    except ET.ParseError:
        return None


def _classify_url(url: str) -> str:
    """
    Very crude URL classifier based on Shopify conventions.
    """
    parsed = urlparse(url)
    path = parsed.path.lower()

    if "/products/" in path:
        return "product"
    if "/collections/" in path:
        # Many product URLs are also under /collections/..., but they'll match /products/ first
        return "collection"
    if "/blogs/" in path:
        return "blog"
    if "/pages/" in path:
        return "page"
    return "other"


def _parse_urlset(root: ET.Element) -> List[Tuple[str, Optional[str]]]:
    """
    Parse a <urlset> sitemap, return list of (loc, lastmod)
    """
    ns = {"sm": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    urls = []
    for url_el in root.findall("sm:url" if ns else "url", ns or None):
        loc_el = url_el.find("sm:loc" if ns else "loc", ns or None)
        if loc_el is None or not loc_el.text:
            continue
        loc = loc_el.text.strip()

        lastmod_el = url_el.find("sm:lastmod" if ns else "lastmod", ns or None)
        lastmod = lastmod_el.text.strip() if (lastmod_el is not None and lastmod_el.text) else None

        urls.append((loc, lastmod))
    return urls


def _parse_sitemapindex(root: ET.Element) -> List[Tuple[str, Optional[str]]]:
    """
    Parse a <sitemapindex> root: fetch each child sitemap and parse URLs.
    """
    ns = {"sm": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    urls: List[Tuple[str, Optional[str]]] = []

    for sm_el in root.findall("sm:sitemap" if ns else "sitemap", ns or None):
        loc_el = sm_el.find("sm:loc" if ns else "loc", ns or None)
        if loc_el is None or not loc_el.text:
            continue
        child_url = loc_el.text.strip()
        child_root = _fetch_xml(child_url)
        if child_root is None:
            continue

        tag_lower = child_root.tag.lower()
        if tag_lower.endswith("urlset"):
            urls.extend(_parse_urlset(child_root))

    return urls


def fetch_sitemap_urls(store_url: str) -> List[Tuple[str, Optional[str]]]:
    """
    Fetch /sitemap.xml and return a list of (loc, lastmod) tuples
    for all URLs in the sitemap (including children if sitemapindex).
    """
    base = normalize_store_url(store_url)
    sitemap_url = base.rstrip("/") + "/sitemap.xml"

    root = _fetch_xml(sitemap_url)
    if root is None:
        raise ShopifyScraperError("sitemap.xml not available or invalid")

    tag_lower = root.tag.lower()

    if tag_lower.endswith("urlset"):
        return _parse_urlset(root)

    if tag_lower.endswith("sitemapindex"):
        urls = _parse_sitemapindex(root)
        if not urls:
            raise ShopifyScraperError("No URLs found in sitemap index")
        return urls

    # Unknown sitemap structure
    raise ShopifyScraperError("Unsupported sitemap.xml structure")


def summarize_sitemap(
    urls_with_lastmod: List[Tuple[str, Optional[str]]],
    max_examples_per_type: int = 5,
) -> Dict[str, Any]:
    """
    Summarize sitemap URLs into counts by type, lastmod stats, and examples.
    """
    by_type_counts: Dict[str, int] = {}
    examples: Dict[str, List[str]] = {}
    lastmods: List[str] = []

    for loc, lastmod in urls_with_lastmod:
        url_type = _classify_url(loc)
        by_type_counts[url_type] = by_type_counts.get(url_type, 0) + 1

        if url_type not in examples:
            examples[url_type] = []
        if len(examples[url_type]) < max_examples_per_type:
            examples[url_type].append(loc)

        if lastmod:
            lastmods.append(lastmod)

    # crude "latest lastmod"
    latest_lastmod = max(lastmods) if lastmods else None

    summary: Dict[str, Any] = {
        "total_urls": int(len(urls_with_lastmod)),
        "by_type": by_type_counts,
        "latest_lastmod": latest_lastmod,
        "example_urls": examples,
    }

    return summary