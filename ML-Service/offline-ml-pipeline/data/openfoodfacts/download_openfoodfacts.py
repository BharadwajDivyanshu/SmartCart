# import pandas as pd
# import json
# from ast import literal_eval # Safer than eval()

# def parse_nutriments(nutri_string):
#     """
#     Safely parses the 'nutriments' string into a dictionary.
#     """
#     try:
#         return literal_eval(nutri_string)
#     except (ValueError, SyntaxError):
#         return {}

# print("📦 TEST RUN: Loading first 1000 rows...")

# try:
#     # --- KEY CHANGE: Added 'nrows=1000' ---
#     df = pd.read_csv(
#         "data/openfoodfacts/en.openfoodfacts.org.products.csv", 
#         sep='\t', 
#         low_memory=False, 
#         nrows=1000  # <--- This tells pandas to stop reading after 1000 rows
#     )
#     print(f"✅ Loaded {len(df)} test rows")

# except FileNotFoundError:
#     print("❌ Error: File not found. Make sure the path is correct.")
#     exit()

# # --- Run the rest of your script normally ---

# # Keep only useful columns
# keep_cols = [
#     "code", "product_name", "nutriments", "image_url", "countries_tags", "brands"
# ]
# df = df.reindex(columns=keep_cols)

# # Drop rows with no product name or nutrients
# df = df.dropna(subset=["product_name", "nutriments"])
# print(f"Rows after dropping NaNs: {len(df)}")


# # Check if we still have data left after filtering
# if not df.empty:
#     # --- Now test the nutrient parsing from the previous step ---
#     print("⚙️ Parsing 'nutriments' column...")
#     df['nutriments_dict'] = df['nutriments'].apply(parse_nutriments)

#     print("⚙️ Extracting nutrient features...")
#     df['proteins_100g'] = df['nutriments_dict'].apply(lambda x: x.get('proteins_100g', 0))
#     df['sugars_100g'] = df['nutriments_dict'].apply(lambda x: x.get('sugars_100g', 0))
#     df['fat_100g'] = df['nutriments_dict'].apply(lambda x: x.get('fat_100g', 0))

#     # Clean up intermediate columns
#     df = df.drop(columns=['nutriments', 'nutriments_dict'])
    
#     # Optional: filter only food sold in the US or India for relevance
#     df = df[df["countries_tags"].str.contains("united-states|india", na=False, case=False)]
#     print(f"Rows after country filter: {len(df)}")

#     # --- KEY CHANGE: Print .head(5) instead of saving ---
#     print("\n✅ Test complete! Displaying first 5 results:")
#     print(df.head(5))

# else:
#     print("\n⚠️ Test complete. No data remained after filtering the first 1000 rows.")
#     print("   This is OK, try increasing 'nrows' to 5000 or 10000 if you see this.")

import requests
import gzip
import shutil
import os
from tqdm import tqdm

# --- Configuration ---
URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.tsv.gz"
DOWNLOAD_DIR = "data/openfoodfacts"
COMPRESSED_FILE = os.path.join(DOWNLOAD_DIR, "en.openfoodfacts.org.products.tsv.gz")
UNCOMPRESSED_FILE = os.path.join(DOWNLOAD_DIR, "en.openfoodfacts.org.products.csv") # Save as .csv to match your next script
# ---------------------

def download_file():
    """Downloads the large file with a progress bar."""
    print(f"📦 Starting download from {URL}...")
    try:
        # Create the directory if it doesn't exist
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        # Use streaming download for large files
        resp = requests.get(URL, stream=True, allow_redirects=True)
        resp.raise_for_status() # Check for HTTP errors
        
        total_size = int(resp.headers.get('content-length', 0))
        
        with open(COMPRESSED_FILE, 'wb') as f, tqdm(
            desc="Downloading",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in resp.iter_content(chunk_size=1024):
                size = f.write(chunk)
                bar.update(size)
                
        print("✅ Download complete.")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading file: {e}")
        return False

def decompress_file():
    """Decompresses the .gz file."""
    print(f"⚙️ Unzipping {COMPRESSED_FILE}...")
    try:
        with gzip.open(COMPRESSED_FILE, 'rb') as f_in:
            with open(UNCOMPRESSED_FILE, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"✅ Unzip complete. File saved to {UNCOMPRESSED_FILE}")
        
        # Clean up the compressed file
        os.remove(COMPRESSED_FILE)
        print(f"🧹 Cleaned up {COMPRESSED_FILE}")
        
    except Exception as e:
        print(f"❌ Error unzipping file: {e}")

if __name__ == "__main__":
    if download_file():
        decompress_file()
    print("🎉 All done. The data is ready for processing.")