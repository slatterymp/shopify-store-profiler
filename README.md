# Shopify Store Profiler

A Python tool for profiling public Shopify stores by using their exposed endpoints, sitemaps, and homepage HTML.  
The profiler generates structured data, visualizations, clustering insights, and an optional Streamlit web interface.

## Features

### Data Extraction
- Product data from `/products.json`
- Collections from `/collections.json`
- Sitemap URLs from `/sitemap.xml`
- Homepage HTML for lightweight tech stack detection

### Analysis
- Product price statistics
- Product type distribution
- Tag frequency analysis
- Collection sizes and product counts
- Sitemap/SEO footprint
- Tech stack identification (Klaviyo, Yotpo, Recharge, etc.)

### Clustering
- Product text vectorization (TF-IDF)
- KMeans clustering
- Cluster summaries (size, average price, example titles)

### Outputs
- `.parquet` and `.csv` product exports  
- `profile.json` summarizing all findings  
- `report.md` human-readable store profile  
- Figures (PNG):
  - Price distribution  
  - Product types  
  - Top tags  
  - Cluster sizes  

### Streamlit UI
A web interface for running analyses interactively and viewing results.

---

## Installation

Clone the repository:
git clone https://github.com/slatterymp/shopify-store-profiler.git
cd shopify-store-profiler

Install dependencies:
pip install -r requirements.txt

(Optional) Create a virtual environment:
python3 -m venv venv
source venv/bin/activate

---

## Command-Line Usage

Run a store profile analysis:
python profile_store.py https://examplestore.com

Results are saved under:
data/<store_slug>/

This directory may include:

- `products.parquet`
- `products_summary.csv`
- `collections.parquet`
- `profile.json`
- `report.md`
- `figures/` (charts)

---

## Streamlit Web App

Launch the UI:
streamlit run app.py

Then open:
http://localhost:8501

The UI provides:

- Overview metrics  
- Price distribution  
- Product type charts  
- Tag analysis  
- Collections overview  
- Sitemap/SEO summary  
- Tech stack detection  
- Product clustering  
- Downloads for CSV/JSON  

---

## Project Structure
shopify-store-profiler/
│
├── app.py
├── profile_store.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── src/
│ ├── shopify_scraper.py
│ ├── analyzer.py
│ ├── reporting.py
│ ├── visuals.py
│ ├── collections_scraper.py
│ ├── sitemap_scraper.py
│ ├── tech_stack.py
│ ├── product_clustering.py
│
├── data/ (output directory, ignored by Git)
│
└── notebooks/
└── 01_store_profile.ipynb


---

## Notes

- Some Shopify stores restrict access to `/products.json` or use rate-limiting.  
- This tool only analyzes publicly available data.  
- Intended for educational, research, and competitive analysis use.  

---

## License

MIT License.
