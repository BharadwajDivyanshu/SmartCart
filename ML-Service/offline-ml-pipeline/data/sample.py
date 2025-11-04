# print_off_filtered_sample.py
import pandas as pd

# --- Configuration ---
off_parquet_path = "data/instacart_product_nutrition.parquet"

# --- Load OFF filtered parquet ---
print(f"📦 Loading filtered OpenFoodFacts dataset from '{off_parquet_path}'...")
off_df = pd.read_parquet(off_parquet_path)

print(f"✅ Loaded {len(off_df)} products.\n")
print("📄 Printing first 20 products:\n")

# --- Print first 20 rows ---
for i, row in off_df.head(5).iterrows():
    print({
        "code": row.get("code"),
        "product_name": row.get("product_name"),
        "images": row.get("images"),
        "nutriments": row.get("nutriments")
    })
