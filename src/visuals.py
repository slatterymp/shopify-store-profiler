# src/visuals.py

import os
from typing import Dict, Any

import pandas as pd
import matplotlib.pyplot as plt


def _save_fig(fig, path: str):
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_price_distribution(df: pd.DataFrame, out_path: str):
    prices = pd.to_numeric(df.get("first_variant_price"), errors="coerce").dropna()
    if prices.empty:
        return

    fig, ax = plt.subplots()
    ax.hist(prices, bins=30)
    ax.set_title("Price distribution (first variant)")
    ax.set_xlabel("Price")
    ax.set_ylabel("Count")
    _save_fig(fig, out_path)


def plot_product_types(df: pd.DataFrame, out_path: str, top_n: int = 15):
    if "product_type" not in df.columns:
        return

    counts = (
        df["product_type"]
        .fillna("")
        .replace("", "Unspecified")
        .value_counts()
        .head(top_n)
    )

    if counts.empty:
        return

    fig, ax = plt.subplots()
    counts.plot(kind="bar", ax=ax)
    ax.set_title(f"Top {top_n} product types")
    ax.set_xlabel("Product type")
    ax.set_ylabel("Count")

    # FIX: rotate & align tick labels the correct way
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    _save_fig(fig, out_path)


def plot_top_tags(profile: Dict[str, Any], out_path: str, top_n: int = 25):
    top_tags = profile.get("top_tags", {})
    if not top_tags:
        return

    # profile["top_tags"] is already sorted when created
    items = list(top_tags.items())[:top_n]
    labels = [k for k, _ in items]
    values = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(labels)), values)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_title(f"Top {top_n} tags")
    ax.set_xlabel("Count")
    _save_fig(fig, out_path)

def plot_cluster_sizes(profile: Dict[str, Any], out_path: str):
    clustering = profile.get("clustering", {})
    clusters = clustering.get("clusters", [])
    if not clusters:
        return

    labels = [f"C{c['cluster_id']}" for c in clusters]
    sizes = [c.get("size", 0) for c in clusters]

    fig, ax = plt.subplots()
    ax.bar(labels, sizes)
    ax.set_title("Cluster sizes")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Number of products")
    _save_fig(fig, out_path)

def generate_figures(
    df: pd.DataFrame,
    profile: Dict[str, Any],
    figures_dir: str,
):
    os.makedirs(figures_dir, exist_ok=True)

    plot_price_distribution(
        df,
        os.path.join(figures_dir, "price_distribution.png"),
    )

    plot_product_types(
        df,
        os.path.join(figures_dir, "product_types.png"),
    )

    plot_top_tags(
        profile,
        os.path.join(figures_dir, "top_tags.png"),
    )

    plot_cluster_sizes(
        profile,
        os.path.join(figures_dir, "cluster_sizes.png"),
    )
