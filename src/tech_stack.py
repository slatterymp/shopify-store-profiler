# src/tech_stack.py

import requests
from typing import Dict, Any, List
from .shopify_scraper import normalize_store_url, ShopifyScraperError


def fetch_homepage_html(store_url: str, timeout: int = 10) -> str:
    base = normalize_store_url(store_url)
    resp = requests.get(base, timeout=timeout)
    if resp.status_code != 200:
        raise ShopifyScraperError(f"Failed to fetch homepage HTML (status {resp.status_code})")
    return resp.text


def _find_any(html: str, needles: List[str]) -> bool:
    html_lower = html.lower()
    return any(n.lower() in html_lower for n in needles)


def detect_tech_stack(html: str) -> Dict[str, Any]:
    """
    Very rough tech stack fingerprinting based on substrings in the HTML.

    Not meant to be perfect; just enough to show:
      - apps
      - pixels
      - possible theme hints
    """
    html_lower = html.lower()

    apps = []

    # Email / CRM
    if _find_any(html, ["klaviyo.js", "klaviyo", "klaviyo_tracking"]):
        apps.append("Klaviyo")
    if _find_any(html, ["omnisend", "omni_send"]):
        apps.append("Omnisend")
    if _find_any(html, ["mailchimp", "mcjs"]):
        apps.append("Mailchimp")

    # Reviews / UGC
    if _find_any(html, ["yotpo", "staticw2.yotpo.com"]):
        apps.append("Yotpo")
    if _find_any(html, ["judge.me", "cdn.judge.me"]):
        apps.append("Judge.me")
    if _find_any(html, ["stamped.io", "stamped-reviews"]):
        apps.append("Stamped.io")

    # Subscriptions
    if _find_any(html, ["recharge.js", "rechargepayments"]):
        apps.append("Recharge")
    if _find_any(html, ["bold-subscriptions", "boldSubscriptions"]):
        apps.append("Bold Subscriptions")

    # Helpdesk / chat
    if _find_any(html, ["gorgias-", "gorgias.io"]):
        apps.append("Gorgias")
    if _find_any(html, ["intercom", "widget.intercom.io"]):
        apps.append("Intercom")
    if _find_any(html, ["zendesk", "zdassets.com"]):
        apps.append("Zendesk")
    if _find_any(html, ["crisp.chat", "client.crisp.im"]):
        apps.append("Crisp chat")

    # Page builders / merchandising
    if _find_any(html, ["shogun", "cdn.getshogun.com"]):
        apps.append("Shogun")
    if _find_any(html, ["pagefly", "cdn.pagefly.io"]):
        apps.append("PageFly")
    if _find_any(html, ["gem_pages", "gempages"]):
        apps.append("GemPages")

    # Analytics / pixels
    pixels = {}
    if _find_any(html, ["gtag('config'", "www.googletagmanager.com/gtag/"]):
        pixels["Google Analytics / gtag"] = True
    if _find_any(html, ["www.googletagmanager.com/gtm.js"]):
        pixels["Google Tag Manager"] = True
    if _find_any(html, ["fbq('init'", "connect.facebook.net/en_US/fbevents.js"]):
        pixels["Facebook Pixel"] = True
    if _find_any(html, ["snaptr('init'", "sc-static.net/scevent.min.js"]):
        pixels["Snap Pixel"] = True
    if _find_any(html, ["tiktokanalytics.js", "analytics.tiktok.com"]):
        pixels["TikTok Pixel"] = True
    if _find_any(html, ["hotjar", "static.hotjar.com"]):
        pixels["Hotjar"] = True

    # Theme hints (super rough)
    theme_hint = None
    if "shopify.theme" in html_lower or "theme_name" in html_lower:
        theme_hint = "Custom / identified in JS"
    if "debut" in html_lower:
        theme_hint = "Possibly Debut theme"
    if "dawn" in html_lower:
        theme_hint = "Possibly Dawn theme"

    return {
        "apps_detected": sorted(set(apps)),
        "pixels": pixels,
        "theme_hint": theme_hint,
    }