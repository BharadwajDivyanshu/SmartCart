import faiss
import numpy as np
import json
import os

# --- Configuration (Should match outputs from triple2vec_train.py) ---
EMBEDDINGS_PATH = "data/embeddings/product_embeddings.npy"
PROD2IDX_PATH = "data/embeddings/product_to_idx.json"
OUTPUT_DIR = "data" # Directory to save the FAISS index
FAISS_INDEX_FILE = os.path.join(OUTPUT_DIR, "faiss_item_index.idx")

# FAISS Index Configuration
FAISS_METRIC = faiss.METRIC_INNER_PRODUCT # Use Inner Product for cosine similarity with normalized vectors
# HNSW is generally a good balance of speed and accuracy
# M=32 is a standard value for the number of connections per layer in HNSW
FAISS_INDEX_TYPE = f"HNSW{32}"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("🚀 Starting FAISS index build process...")

# --- 1. Load Pre-computed Product Embeddings ---
try:
    print(f"📦 Loading product embeddings from: {EMBEDDINGS_PATH}")
    product_embeddings = np.load(EMBEDDINGS_PATH)
    # Ensure embeddings are in float32 format, required by FAISS
    product_embeddings = product_embeddings.astype('float32')
    num_products, embed_dim = product_embeddings.shape
    print(f"✅ Loaded {num_products} product embeddings with dimension {embed_dim}.")
except FileNotFoundError:
    print(f"❌ Error: Embeddings file not found at '{EMBEDDINGS_PATH}'.")
    print("➡ Please run 'triple2vec_train.py' first to generate embeddings.")
    exit()
except Exception as e:
    print(f"❌ Error loading embeddings: {e}")
    exit()

# --- 2. Load Product-to-Index Mapping (Optional but recommended for verification) ---
try:
    with open(PROD2IDX_PATH, 'r') as f:
        prod2idx = json.load(f)
    print(f"✅ Loaded product-to-index mapping from: {PROD2IDX_PATH}")
    # Sanity check: Ensure mapping size matches embedding count
    if len(prod2idx) != num_products:
        print(f"⚠️ Warning: Number of products in mapping ({len(prod2idx)}) does not match embeddings count ({num_products}).")
except FileNotFoundError:
    print(f"⚠️ Warning: Product-to-index mapping file not found at '{PROD2IDX_PATH}'. Index will be built, but mapping verification skipped.")
except Exception as e:
    print(f"⚠️ Warning: Error loading product mapping: {e}")


# --- 3. Normalize Embeddings for Cosine Similarity ---
# Normalizing ensures that Inner Product search is equivalent to Cosine Similarity
print("📏 Normalizing embeddings (L2 normalization)...")
faiss.normalize_L2(product_embeddings)
print("✅ Embeddings normalized.")

# --- 4. Build the FAISS Index ---
print(f"🛠️ Building FAISS index ({FAISS_INDEX_TYPE}, Metric: {FAISS_METRIC})...")
# Use IndexFactory for flexibility, HNSWFlat is efficient
index = faiss.index_factory(embed_dim, FAISS_INDEX_TYPE, FAISS_METRIC)

# Check if the index needs training (some index types do, HNSWFlat does not)
if not index.is_trained:
    print("   Index requires training...")
    # Training is usually done on a subset of data for indexes like IVFFlat
    # HNSWFlat does not require a separate training step.
    # index.train(product_embeddings) # Uncomment if using an index that needs training
    pass # HNSWFlat doesn't need explicit training

print(f"➕ Adding {num_products} vectors to the index...")
index.add(product_embeddings)
print(f"✅ Index built successfully. Total vectors in index: {index.ntotal}")

# --- 5. Save the Index ---
print(f"💾 Saving FAISS index to: {FAISS_INDEX_FILE}")
faiss.write_index(index, FAISS_INDEX_FILE)
print("🎉 FAISS index build complete!")
