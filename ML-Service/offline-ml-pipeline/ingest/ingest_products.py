import pandas as pd
from sqlalchemy import create_engine, text
import os
import json
from dotenv import load_dotenv
from tqdm import tqdm

# --- CONFIGURATION ---
# 1. Your enriched file that is MISSING product_id
PARQUET_PATH = "../../ml_models/products_with_nutrition_and_health_10k.parquet" 
# 2. The original Kaggle products file that HAS product_id
KAGGLE_PRODUCTS_PATH = "../data/kaggle/products.csv"
# 3. Path to your backend .env file
ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', '.env')

print("🚀 Starting Product Ingestion Script (with ID patching)...")

# --- 1. LOAD DATABASE URL ---
load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print(f"❌ Error: Could not find DATABASE_URL in {ENV_PATH}")
    exit()
print("✅ Loaded database configuration.")

# --- 2. LOAD BOTH DATA FILES ---
try:
    df_enriched = pd.read_parquet(PARQUET_PATH)
    print(f"✅ Loaded enriched data ({len(df_enriched)} rows) from '{PARQUET_PATH}'.")
    
    df_original_products = pd.read_csv(KAGGLE_PRODUCTS_PATH)
    print(f"✅ Loaded original product data ({len(df_original_products)} rows) from '{KAGGLE_PRODUCTS_PATH}'.")
except FileNotFoundError as e:
    print(f"❌ Error: File not found. {e}")
    exit()
except Exception as e:
    print(f"❌ Error loading data: {e}")
    exit()

# --- 3. PATCH THE DATA (JOIN TO GET MISSING product_id) ---
print("🔧 Patching data: Joining enriched file with original file to get product_id...")

# Prepare the original data: we only need 'product_id' and 'product_name'
df_original_products = df_original_products[['product_id', 'product_name']]

# Join the two dataframes
# We join your enriched file's 'instacart_product' column
# with the original file's 'product_name' column.
df_patched = df_enriched.merge(
    df_original_products,
    left_on='instacart_product',
    right_on='product_name',
    how='left'
)

# Check if the join was successful
missing_ids = df_patched['product_id'].isna().sum()
if missing_ids > 0:
    print(f"⚠️ Warning: {missing_ids} products could not be matched back to an original product_id.")
df_patched = df_patched.dropna(subset=['product_id']) # Drop rows we couldn't match
print(f"✅ Data patched. {len(df_patched)} products successfully matched with an ID.")

# --- 4. TRANSFORM DATA TO MATCH 'schema.prisma' ---
print("🔄 Transforming data to match database schema...")

# Map the *actual* column names from your patched file to the *target* names in schema.prisma
column_rename_map = {
    'product_id': 'productId',         # The CRITICAL integer ID (now present)
    'instacart_product': 'productName',# The product's name
    'image_url': 'imageUrl',
    'nutrients': 'nutriments',         # Your file has 'nutrients'
    'health_factor': 'healthFactorScore' # Your file has 'health_factor'
}

df_final = df_patched.rename(columns=column_rename_map)

# Add missing optional columns from schema with default values
if 'category' not in df_final.columns:
    df_final['category'] = 'Grocery'
if 'price' not in df_final.columns:
    df_final['price'] = 1.99 # Add a default price

# Select only the columns that are in your 'Product' model
final_columns = [
    'productId', 'productName', 'category', 'price', 
    'imageUrl', 'nutriments', 'healthFactorScore'
]
df_final = df_final[final_columns]

# Convert 'nutriments' dict to JSON string for database insertion
def safe_json_dump(data):
    if isinstance(data, str):
        try: json.loads(data); return data
        except (json.JSONDecodeError, TypeError): return None
    if data and isinstance(data, dict):
        return json.dumps(data)
    return None

df_final['nutriments'] = df_final['nutriments'].apply(safe_json_dump)

# Ensure productId is an integer (it might be float after merge)
df_final['productId'] = df_final['productId'].astype(int)

print("✅ Data transformation complete.")

# --- 5. CONNECT AND INGEST TO POSTGRESQL (FIXED) ---
try:
    print("Connecting to PostgreSQL database...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        with conn.begin(): # Start a transaction
            print("Clearing existing data (CartItem, Product)...")
            # We must delete from the "child" table (CartItem) first
            conn.execute(text('DELETE FROM "CartItem";'))
            # Now we can safely delete from the "parent" table (Product)
            conn.execute(text('DELETE FROM "Product";'))
        print("✅ Existing tables cleared.")

    print(f"Ingesting {len(df_final)} products into 'Product' table...")
    # Now we use 'append' since the table is empty but still exists
    df_final.to_sql(
        'Product', 
        con=engine, 
        if_exists='append', # Changed from 'replace' to 'append'
        index=False,
        chunksize=1000
    )
    
    print("\n🎉 SUCCESS! Your 'Product' table has been populated.")
    print("Your Node.js backend can now fetch product details.")

except Exception as e:
    print(f"\n❌ An error occurred during database ingestion:")
    print(e)
    print("\n   Please ensure your PostgreSQL server is running and the DATABASE_URL is correct.")

