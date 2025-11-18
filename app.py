# app.py

import os
import streamlit as st
import pandas as pd

from src.reporting import generate_store_report, store_slug_from_url
from src.shopify_scraper import normalize_store_url


# --- Streamlit page config ---
st.set_page_config(
    page_title="Shopify Store Profiler",
    layout="wide",
)


st.title("🛍️ Shopify Store Profiler")
st.write("Profile any public Shopify store. Powered by your local machine.")


# --- Input form ---
with st.form("url_form"):
    store_url = st.text_input(
        "Enter Shopify store URL:",
        placeholder="https://examplestore.com",
    )
    submitted = st.form_submit_button("Analyze Store")


if submitted and store_url.strip():
    # Normalize URL
    store_url = normalize_store_url(store_url)

    # Run profiling
    with st.spinner("Profiling store..."):
        profile = generate_store_report(store_url)
        slug = store_slug_from_url(store_url)
        base_path = os.path.join("data", slug)

    st.success("Analysis complete!")
    st.subheader(f"Store: {store_url}")

    # --- Overview ---
    st.header("📊 Overview")
    st.write(f"**Products:** {profile.get('n_products')}")
    st.write(profile.get("price_stats"))

    # Load product dataframe (saved earlier)
    df = pd.read_parquet(os.path.join(base_path, "products.parquet"))

    st.write("### Product Summary")
    st.dataframe(df.head(20))

    # --- Price distribution ---
    st.header("💰 Price Distribution")
    price_chart_path = os.path.join(base_path, "figures", "price_distribution.png")
    if os.path.exists(price_chart_path):
        st.image(price_chart_path, use_column_width=True)

    # --- Product types ---
    st.header("📦 Product Types")
    pt_chart_path = os.path.join(base_path, "figures", "product_types.png")
    if os.path.exists(pt_chart_path):
        st.image(pt_chart_path, use_column_width=True)

    # --- Top tags ---
    st.header("🏷️ Top Tags")
    tag_chart_path = os.path.join(base_path, "figures", "top_tags.png")
    if os.path.exists(tag_chart_path):
        st.image(tag_chart_path, use_column_width=True)

    # --- Collections ---
    st.header("📚 Collections")
    if profile.get("collections"):
        st.json(profile["collections"])
        c_path = os.path.join(base_path, "collections.parquet")
        if os.path.exists(c_path):
            dfc = pd.read_parquet(c_path)
            st.dataframe(dfc[["title", "handle", "products_count"]].head(50))

    # --- Sitemap / SEO ---
    st.header("🗺️ SEO / Sitemap Overview")
    if profile.get("sitemap"):
        st.json(profile["sitemap"])

    # --- Tech stack ---
    st.header("🔧 Tech Stack Detected")
    if profile.get("tech_stack"):
        st.json(profile["tech_stack"])

    # --- Clustering ---
    st.header("🧩 Product Clusters")
    if profile.get("clustering") and profile["clustering"].get("clusters"):
        st.json(profile["clustering"])

        cluster_chart_path = os.path.join(base_path, "figures", "cluster_sizes.png")
        if os.path.exists(cluster_chart_path):
            st.image(cluster_chart_path, use_column_width=True)

        # Show product sample per cluster
        st.write("### Sample products per cluster")
        if "cluster" in df.columns:
            for cid in sorted(df["cluster"].unique()):
                st.write(f"**Cluster {cid}**")
                st.dataframe(df[df["cluster"] == cid].head(10))

    # --- Downloads ---
    st.header("⬇️ Downloads")
    st.download_button(
        "Download profile.json",
        data=open(os.path.join(base_path, "profile.json"), "rb").read(),
        file_name=f"{slug}_profile.json",
        mime="application/json",
    )
    st.download_button(
        "Download products_summary.csv",
        data=open(os.path.join(base_path, "products_summary.csv"), "rb").read(),
        file_name=f"{slug}_products_summary.csv",
        mime="text/csv",
    )