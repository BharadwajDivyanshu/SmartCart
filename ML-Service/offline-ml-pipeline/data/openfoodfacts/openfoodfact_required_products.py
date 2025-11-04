import pandas as pd

# Paths
instacart_path = "data/instacart_product_nutrition.parquet"
off_full_path = "data/openfoodfacts_full.csv"  # Your full OFF CSV (if available)
filtered_off_path = "data/openfoodfacts_filtered.csv"

# Load Instacart mapped data
instacart_df = pd.read_parquet(instacart_path)
needed_codes = instacart_df['matched_off_code'].astype(str).unique()
print(f"ℹ️ Total unique OFF codes needed: {len(needed_codes)}")

# Filter OFF dataset in chunks
chunk_size = 500_000
filtered_chunks = []

for chunk in pd.read_csv(off_full_path, chunksize=chunk_size, dtype={'code': str}):
    filtered = chunk[chunk['code'].isin(needed_codes)]
    if not filtered.empty:
        filtered_chunks.append(filtered)

if filtered_chunks:
    off_filtered = pd.concat(filtered_chunks, ignore_index=True)
    off_filtered.to_csv(filtered_off_path, index=False)
    print(f"✅ Filtered OFF dataset saved: {len(off_filtered)} products")
else:
    print("⚠️ No matching OFF products found in the dataset.")