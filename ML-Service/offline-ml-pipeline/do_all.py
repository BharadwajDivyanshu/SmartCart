import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from rapidfuzz import process, fuzz
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------- CONFIG ---------------- #
INSTACART_PRODUCTS_FILE = "data/kaggle/products.csv"
OPENFOODFACTS_FILE = "data/openfoodfacts/en.openfoodfacts.org.products.csv"
OUTPUT_PARQUET_FILE = "data/products_with_nutrition_and_health_10k.parquet"

KEEP_COLS = [
    "code", "product_name", "image_url", "countries_tags", "brands",
    "proteins_100g", "fat_100g", "carbohydrates_100g",
    "sugars_100g", "fiber_100g", "salt_100g"
]

MATCH_THRESHOLD = 85
IDEAL_NUTRIENTS = {"protein": 10.0, "fat": 10.0, "carbs": 30.0}
CHUNK_SIZE = 500_000  # adjust for memory
MAX_INSTACART = 10_000  # first 10k products
NUM_THREADS = 4  # adjust based on your CPU
# ---------------------------------------- #

def compute_health_factor(nutrients: dict):
    if not nutrients:
        return None
    try:
        p = float(nutrients.get("proteins_100g") or 0)
        f = float(nutrients.get("fat_100g") or 0)
        c = float(nutrients.get("carbohydrates_100g") or 0)
        deviation = np.sqrt((p - IDEAL_NUTRIENTS["protein"])**2 +
                            (f - IDEAL_NUTRIENTS["fat"])**2 +
                            (c - IDEAL_NUTRIENTS["carbs"])**2)
        return round(max(0.0, 1.0 - deviation / 100.0), 3)
    except (ValueError, TypeError):
        return None

def match_product(product_name, product_lower, off_groups):
    if not product_lower:
        return {
            "instacart_product": product_name,
            "matched_off_product": None,
            "match_score": None,
            "image_url": None,
            "brands": None,
            "nutrients": None,
            "health_factor": None,
            "off_code": None,
            "countries_tags": None,
        }

    # First 2-letter filtering
    prefix = product_lower[:2]
    candidates_df = off_groups.get(prefix, pd.DataFrame(columns=KEEP_COLS + ["product_name_lower"]))
    candidates_names = candidates_df["product_name_lower"].tolist()

    # Exact match first
    if product_lower in candidates_names:
        idx = candidates_names.index(product_lower)
        matched_row = candidates_df.iloc[idx]
        score = 100
    else:
        # RapidFuzz matching
        match_data = process.extractOne(product_lower, candidates_names, scorer=fuzz.WRatio)
        if not match_data or match_data[1] < MATCH_THRESHOLD:
            return {
                "instacart_product": product_name,
                "matched_off_product": None,
                "match_score": None,
                "image_url": None,
                "brands": None,
                "nutrients": None,
                "health_factor": None,
                "off_code": None,
                "countries_tags": None,
            }
        _, score, idx = match_data
        matched_row = candidates_df.iloc[idx]

    nutrients = {col: matched_row[col] for col in ["proteins_100g","fat_100g","carbohydrates_100g",
                                                   "sugars_100g","fiber_100g","salt_100g"]}
    health_factor = compute_health_factor(nutrients)

    return {
        "instacart_product": product_name,
        "matched_off_product": matched_row["product_name"],
        "match_score": round(score, 2),
        "image_url": matched_row["image_url"],
        "brands": matched_row["brands"],
        "nutrients": nutrients,
        "health_factor": health_factor,
        "off_code": matched_row["code"],
        "countries_tags": matched_row["countries_tags"],
    }

def main():
    print("📊 Loading Instacart products...")
    instacart_df = pd.read_csv(INSTACART_PRODUCTS_FILE).head(MAX_INSTACART)
    instacart_df["product_name_lower"] = instacart_df["product_name"].astype(str).str.lower().str.strip()
    print(f"✅ Loaded {len(instacart_df)} Instacart products")

    # Prepare OFF groups with first 2 letters
    off_groups = {}
    print("📦 Processing OpenFoodFacts CSV in chunks...")
    for chunk in tqdm(pd.read_csv(OPENFOODFACTS_FILE, sep='\t', usecols=KEEP_COLS, dtype=str,
                                  low_memory=False, chunksize=CHUNK_SIZE, on_bad_lines='skip'),
                      desc="Loading OFF"):
        chunk = chunk.dropna(subset=["product_name"]).copy()
        chunk["product_name_lower"] = chunk["product_name"].str.lower().str.strip()
        chunk["prefix2"] = chunk["product_name_lower"].str[:2]
        for prefix, df in chunk.groupby("prefix2"):
            if prefix in off_groups:
                off_groups[prefix] = pd.concat([off_groups[prefix], df], ignore_index=True)
            else:
                off_groups[prefix] = df.copy()

    print(f"✅ Prepared {sum(len(df) for df in off_groups.values())} OFF products in groups")

    enriched_rows = []
    print("\n🔍 Matching and enriching products with parallelism...")

    # Use ThreadPoolExecutor for parallel matching
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(match_product, pname, plower, off_groups)
                   for pname, plower in zip(instacart_df["product_name"], instacart_df["product_name_lower"])]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Enriching"):
            enriched_rows.append(future.result())

    enriched_df = pd.DataFrame(enriched_rows)
    print(f"\n✅ Enriched {enriched_df['matched_off_product'].notna().sum()} / {len(enriched_df)} products successfully")

    os.makedirs(os.path.dirname(OUTPUT_PARQUET_FILE), exist_ok=True)
    enriched_df.to_parquet(OUTPUT_PARQUET_FILE, index=False)
    print(f"💾 Saved enriched dataset to: {OUTPUT_PARQUET_FILE}")

if __name__ == "__main__":
    main()