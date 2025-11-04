# enrich_script_fast_debug.py
import pandas as pd
import numpy as np
from compute_health_factor import compute_hf
import json
import os
from tqdm import tqdm

# --- Configuration ---
input_parquet_path = "data/instacart_product_nutrition.parquet"
off_parquet_path = "data/openfoodfacts_filtered/openfoodfacts_filtered.parquet"
output_parquet_path = "data/products_with_health_score_debug.parquet"

print("🚀 Starting SmartCart ML data enrichment pipeline (debug version)...")

# --- Load Instacart↔OFF mapped data ---
instacart_df = pd.read_parquet(input_parquet_path)
print(f"✅ Loaded Instacart↔OFF mapped data ({len(instacart_df)} rows).")

# --- Load OFF data ---
off_df = pd.read_parquet(off_parquet_path, columns=['code', 'images'])
print(f"📦 Loaded OpenFoodFacts data ({len(off_df)} rows).")

# --- Ensure types match for merge ---
instacart_df['matched_off_code'] = instacart_df['matched_off_code'].astype(str)
off_df['code'] = off_df['code'].astype(str)

# --- Check overlap between datasets ---
instacart_codes = set(instacart_df['matched_off_code'])
off_codes = set(off_df['code'])
intersection = instacart_codes.intersection(off_codes)

print(f"🔍 Matching stats:")
print(f"   • Instacart mapped codes: {len(instacart_codes)}")
print(f"   • OFF available codes:    {len(off_codes)}")
print(f"   • Overlapping codes:      {len(intersection)} "
      f"({len(intersection)/len(instacart_codes)*100:.2f}%)\n")

# --- Extract first image id ---
def extract_imgid(images):
    if isinstance(images, list) and len(images) > 0 and isinstance(images[0], dict):
        return images[0].get('imgid')
    return None

off_df['imgid'] = off_df['images'].map(extract_imgid)

# --- Build image URLs ---
def build_image_url(code, imgid):
    if pd.isna(imgid) or not isinstance(code, str):
        return None
    if len(code) > 8:
        code_path = f"{code[:3]}/{code[3:6]}/{code[6:9]}/{code[9:]}"
    else:
        code_path = code
    return f"https://images.openfoodfacts.org/images/products/{code_path}/{imgid}.400.jpg"

off_df['image_url'] = [build_image_url(c, i) for c, i in zip(off_df['code'], off_df['imgid'])]

# --- Simplify and remove duplicates ---
off_df_simple = off_df[['code', 'image_url']].drop_duplicates(subset=['code'])

# --- Merge with Instacart data ---
print("🔗 Merging image URLs into main dataset...")
merged_df = instacart_df.merge(
    off_df_simple,
    left_on='matched_off_code',
    right_on='code',
    how='left'
).drop(columns=['code'])

missing_images = merged_df['image_url'].isna().sum()
print(f"⚠️ {missing_images:,} products have no image URL "
      f"({missing_images/len(merged_df)*100:.2f}%).")

# --- Parse nutriments and compute health factor ---
def parse_nutriments(nut):
    if isinstance(nut, dict):
        return nut
    try:
        return json.loads(nut) if isinstance(nut, str) else None
    except (json.JSONDecodeError, TypeError):
        return None

merged_df['nutriments_parsed'] = merged_df['nutriments'].map(parse_nutriments)

def compute_hf_safe(nut_dict):
    try:
        return compute_hf(nut_dict) if nut_dict is not None else np.nan
    except Exception:
        return np.nan

tqdm.pandas(desc="⚙️ Computing health factor")
merged_df['health_factor_score'] = merged_df['nutriments_parsed'].progress_apply(compute_hf_safe)
merged_df.drop(columns=['nutriments_parsed'], inplace=True)

# --- Save enriched data ---
os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
merged_df.to_parquet(output_parquet_path, index=False)
print(f"✅ Enriched data saved to '{output_parquet_path}'")

# --- Sample output ---
print("\n--- SAMPLE OUTPUT ---")
print(merged_df[["product_name", "matched_off_code", "image_url", "health_factor_score"]].head(10))
print("----------------------")

# --- Extra debugging info ---
unmatched_codes = merged_df.loc[merged_df['image_url'].isna(), 'matched_off_code'].unique()
print(f"⚠️ Sample unmatched OFF codes: {unmatched_codes[:10]}")
print(f"\n🏁 Pipeline completed successfully.")