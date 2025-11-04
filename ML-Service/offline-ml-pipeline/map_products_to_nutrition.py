import pandas as pd
import numpy as np
import difflib
import json
from tqdm import tqdm
import math

# ---------------- CONFIG ---------------- #
input_instacart_path = "data/instacart_product_nutrition.parquet"
openfoodfacts_path = "data/openfoodfacts_filtered/openfoodfacts_filtered.parquet"
output_path = "data/products_with_nutrition_and_health.parquet"
# ---------------------------------------- #


# ✅ Compute string similarity
def find_best_match(name, candidates, cutoff=0.85):
    if not isinstance(name, str) or name.strip() == "":
        return None
    matches = difflib.get_close_matches(name.lower(), candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None


# ✅ Extract nutrients safely
def extract_nutrients(nutriments):
    """Extract relevant nutrient values from a dict."""
    if isinstance(nutriments, str):
        try:
            nutriments = json.loads(nutriments)
        except Exception:
            return None

    if not isinstance(nutriments, dict):
        return None

    return {
        "energy_kcal_100g": nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal_value"),
        "fat_100g": nutriments.get("fat_100g"),
        "saturated_fat_100g": nutriments.get("saturated-fat_100g"),
        "carbohydrates_100g": nutriments.get("carbohydrates_100g"),
        "sugars_100g": nutriments.get("sugars_100g"),
        "fiber_100g": nutriments.get("fiber_100g"),
        "proteins_100g": nutriments.get("proteins_100g"),
        "salt_100g": nutriments.get("salt_100g"),
    }


# ✅ Extract valid image URL
def extract_image_url(code, images):
    """Return a valid OpenFoodFacts image URL."""
    if not code:
        return None

    base = "https://images.openfoodfacts.org/images/products"

    # Try to format product code as segmented path (OFF style)
    code_str = str(code)
    code_path = "/".join([code_str[i:i + 3] for i in range(0, len(code_str), 3)])

    if isinstance(images, str):
        try:
            images = json.loads(images)
        except Exception:
            return None

    if isinstance(images, dict):
        # Try the 'front' image field
        front = images.get("front")
        if isinstance(front, dict):
            if "display" in front:
                return front["display"]
            elif "small" in front:
                return front["small"]
        # If not, try a generic fallback
        return f"{base}/{code_path}/front_en.400.jpg"

    return f"{base}/{code_path}/front_en.400.jpg"


# ✅ Compute Health Factor
def compute_health_factor(nutrients):
    """
    Compute a simple health score based on macro balance.
    Higher protein & fiber = better.
    High sugar, salt, and saturated fat = worse.
    """
    if not nutrients or not isinstance(nutrients, dict):
        return None

    # Extract with defaults
    protein = nutrients.get("proteins_100g") or 0
    fiber = nutrients.get("fiber_100g") or 0
    sugar = nutrients.get("sugars_100g") or 0
    sat_fat = nutrients.get("saturated_fat_100g") or 0
    salt = nutrients.get("salt_100g") or 0

    # Scale into 0–100
    score = (
        (protein * 2 + fiber * 1.5)
        - (sugar * 1.2 + sat_fat * 1.0 + salt * 1.3)
    )

    # Normalize and cap
    score = max(0, min(100, 50 + score))
    return round(score, 2)


# ---------------- MAIN ---------------- #
print("🚀 Loading data...")

instacart_df = pd.read_parquet(input_instacart_path)
off_df = pd.read_parquet(openfoodfacts_path)

print(f"✅ Loaded {len(instacart_df)} Instacart items and {len(off_df)} OpenFoodFacts entries")

# Keep only relevant columns
off_df = off_df[["product_name", "nutriments", "images", "code"]].dropna(subset=["product_name"])
off_names = off_df["product_name"].str.lower().tolist()

enriched_rows = []

print("🔍 Matching and enriching products...")

for _, row in tqdm(instacart_df.iterrows(), total=len(instacart_df)):
    product_name = row["product_name"]
    best_match = find_best_match(product_name, off_names, cutoff=0.85)

    if best_match:
        matched_row = off_df[off_df["product_name"].str.lower() == best_match].iloc[0]
        nutrients = extract_nutrients(matched_row["nutriments"])
        img_url = extract_image_url(matched_row["code"], matched_row["images"])
        health_factor = compute_health_factor(nutrients)

        enriched_rows.append({
            "instacart_product": product_name,
            "matched_off_product": matched_row["product_name"],
            "off_code": matched_row["code"],
            "image_url": img_url,
            "nutrients": nutrients,
            "health_factor": health_factor
        })
    else:
        enriched_rows.append({
            "instacart_product": product_name,
            "matched_off_product": None,
            "off_code": None,
            "image_url": None,
            "nutrients": None,
            "health_factor": None
        })

# Convert to DataFrame
enriched_df = pd.DataFrame(enriched_rows)

print(f"\n✅ Enriched {enriched_df['matched_off_product'].notna().sum()} / {len(enriched_df)} products successfully")

# Save as Parquet
enriched_df.to_parquet(output_path, index=False)
print(f"💾 Saved enriched dataset to: {output_path}")

# Optional preview
print("\n📊 Sample:")
print(enriched_df.head(10))