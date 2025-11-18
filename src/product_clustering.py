# src/product_clustering.py

from typing import Dict, Any, List, Tuple

import pandas as pd


class ProductClusteringError(Exception):
    pass


def cluster_products(
    df: pd.DataFrame,
    n_clusters: int | None = None,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Add a 'cluster' column to the DataFrame using TF-IDF + KMeans on
    product title + description, and return a clustering summary dict.

    Returns:
        df_with_clusters, clustering_summary
    """
    # Lazy import so the rest of the project doesn't explode if sklearn is missing
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
    except ImportError as e:
        raise ProductClusteringError(
            "scikit-learn is required for product clustering. Install with "
            "`pip install scikit-learn`."
        ) from e

    # Build text corpus
    title = df.get("title", "").astype(str)
    body = df.get("body_html", "").astype(str)
    texts = (title + " " + body).fillna("").tolist()

    # Not enough data to cluster
    if len(texts) < 5:
        raise ProductClusteringError("Not enough products to perform clustering.")

    # Vectorize text
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words="english",
    )
    X = vectorizer.fit_transform(texts)

    # Choose number of clusters heuristically if not provided
    n_docs = X.shape[0]
    if n_clusters is None:
        # Between 2 and 10 clusters, depending on store size
        n_clusters = max(2, min(10, n_docs // 30))
    if n_clusters > n_docs:
        n_clusters = n_docs

    # KMeans clustering
    km = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10,
    )
    labels = km.fit_predict(X)

    df = df.copy()
    df["cluster"] = labels

    # Build summary per cluster
    clusters_info: List[Dict[str, Any]] = []
    price_col = "first_variant_price" if "first_variant_price" in df.columns else None

    for cid in range(n_clusters):
        cluster_df = df[df["cluster"] == cid]
        size = int(len(cluster_df))

        # avg price
        avg_price = None
        if price_col:
            prices = pd.to_numeric(cluster_df[price_col], errors="coerce").dropna()
            if not prices.empty:
                avg_price = float(prices.mean())

        # top product types
        top_types = {}
        if "product_type" in cluster_df.columns:
            top_types = (
                cluster_df["product_type"]
                .fillna("")
                .replace("", "Unspecified")
                .value_counts()
                .head(5)
                .to_dict()
            )

        # example titles
        example_titles = (
            cluster_df["title"].astype(str).dropna().head(5).tolist()
            if "title" in cluster_df.columns
            else []
        )

        clusters_info.append(
            {
                "cluster_id": cid,
                "size": size,
                "avg_price": avg_price,
                "top_product_types": top_types,
                "example_titles": example_titles,
            }
        )

    summary: Dict[str, Any] = {
        "n_clusters": n_clusters,
        "clusters": clusters_info,
    }

    return df, summary