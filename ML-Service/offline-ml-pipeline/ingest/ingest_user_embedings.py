import torch
import json
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from model import Triple2Vec # Assumes model.py is in the same folder

# --- CONFIGURATION ---
MODEL_PATH = "ml_models/triple2vec_model.pth"
USER_MAP_PATH = "data/embeddings/user2idx.json" # Adjust path if needed
ENV_PATH = os.path.join(os.path.dirname(__file__), '..', 'smartcart-backend', '.env')

# --- Model parameters (MUST match training script) ---
NUM_USERS = 206209
NUM_PRODUCTS = 10000
EMBED_DIM = 64

print("🚀 Starting User Embedding Ingestion Script...")

# --- 1. LOAD DATABASE URL ---
load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print(f"❌ Error: Could not find DATABASE_URL in {ENV_PATH}")
    exit()

# --- 2. LOAD USER MAPPING ---
try:
    with open(USER_MAP_PATH, 'r') as f:
        # Load and convert keys to integers
        user2idx = {int(k): v for k, v in json.load(f).items()}
    # Create the reverse mapping: index -> original user ID
    idx2user = {v: k for k, v in user2idx.items()}
    print(f"✅ Loaded user mapping for {len(user2idx)} users.")
except FileNotFoundError:
    print(f"❌ Error: User mapping file not found at '{USER_MAP_PATH}'.")
    print("   Cannot populate UserEmbedding table without this file.")
    exit()
except Exception as e:
    print(f"❌ Error loading user mapping: {e}")
    exit()

# --- 3. LOAD MODEL & EXTRACT EMBEDDINGS ---
try:
    model = Triple2Vec(NUM_USERS, NUM_PRODUCTS, EMBED_DIM)
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()
    user_embeddings = model.h.weight.data.cpu().numpy()
    print(f"✅ Loaded user embeddings from model. Shape: {user_embeddings.shape}")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit()

# --- 4. PREPARE DATA FOR DATABASE ---
data_to_ingest = []
for index, user_id in idx2user.items():
    if index < len(user_embeddings):
        vector = user_embeddings[index]
        data_to_ingest.append({
            "instacartUserId": int(user_id),
            "embeddingVector": json.dumps(vector.tolist()) # Convert vector to JSON string
        })

df_embeddings = pd.DataFrame(data_to_ingest)

# --- 5. CONNECT AND INGEST TO POSTGRESQL ---
try:
    print("Connecting to PostgreSQL database...")
    engine = create_engine(DATABASE_URL)
    
    print(f"Ingesting {len(df_embeddings)} user embeddings into 'UserEmbedding' table...")
    df_embeddings.to_sql(
        'UserEmbedding', 
        con=engine, 
        if_exists='replace', 
        index=False,
        chunksize=1000
    )
    
    print("\n🎉 SUCCESS! Your 'UserEmbedding' table has been populated.")

except Exception as e:
    print(f"\n❌ An error occurred during database ingestion:")
    print(e)
