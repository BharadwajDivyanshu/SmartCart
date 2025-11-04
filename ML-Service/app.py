# import os
# import faiss
# import numpy as np
# import pandas as pd
# import torch
# import json

# from flask import Flask, request, jsonify
# from model import Triple2Vec # Import the model class

# # --- 1. INITIALIZATION ---
# print("Initializing Flask ML Service...")

# # Create the Flask application
# app = Flask(__name__)

# # --- 2. LOAD ML ARTIFACTS ON STARTUP ---
# # This section loads all necessary files into memory when the server starts.
# # This ensures that API requests are fast and don't have to wait for file I/O.

# MODEL_DIR = 'ml_models'
# N_CANDIDATES = 100 # The number of initial candidates to retrieve from FAISS

# def load_artifacts():
#     """Loads all ML models and data from disk into global variables."""
#     global faiss_index, user_embeddings, item_embeddings, product_health_factors, user2idx, prod2idx

#     # Load FAISS index
#     faiss_index_path = os.path.join(MODEL_DIR, 'faiss_item_index.idx')
#     print(f"Loading FAISS index from {faiss_index_path}...")
#     faiss_index = faiss.read_index(faiss_index_path)

#     # Load the trained Triple2Vec model weights
#     model_path = os.path.join(MODEL_DIR, 'triple2vec_model.pth')
#     print(f"Loading model weights from {model_path}...")
    
#     # You MUST know these values from your training script to initialize the model class
#     # These should be saved as artifacts after training. Using placeholders for now.
#     # TODO: Replace with actual values from your training run
#     num_users = 206209 
#     num_products = 49688
#     embedding_dim = 128

#     model = Triple2Vec(num_users, num_products, embedding_dim)
#     model.load_state_dict(torch.load(model_path, map_location="cpu"))
#     model.eval() # Set model to evaluation mode

#     # Extract embedding weights into NumPy arrays for efficient computation
#     user_embeddings = model.h.weight.data.cpu().numpy()
#     item_p = model.p.weight.data.cpu().numpy()
#     item_q = model.q.weight.data.cpu().numpy()
#     # Combine item embeddings just like in build_faiss.py
#     item_embeddings = (item_p + item_q) / 2.0
#     faiss.normalize_L2(item_embeddings) # Normalize for dot product similarity

#     # Load the product nutrition and health factor data
#     nutrition_path = os.path.join(MODEL_DIR, 'products_with_nutrition_and_health_10k.parquet')
#     print(f"Loading product health data from {nutrition_path}...")
#     product_df = pd.read_parquet(nutrition_path)
#     # Store health factors in a simple dictionary for fast lookups
#     product_health_factors = dict(zip(product_df['product_id'], product_df['health_factor_score']))
    
#     # TODO: Load your user_id -> index and product_id -> index mapping files
#     # These are critical for mapping the IDs from the Node.js service to the correct embedding index.
#     # For now, we will assume the IDs passed are already the correct indices.
#     # with open(os.path.join(MODEL_DIR, 'user2idx.json'), 'r') as f:
#     #     user2idx = json.load(f)
#     # with open(os.path.join(MODEL_DIR, 'prod2idx.json'), 'r') as f:
#     #     prod2idx = json.load(f)

#     print("✅ ML artifacts loaded successfully.")

# # --- 3. DEFINE THE RECOMMENDATION API ENDPOINT ---
# @app.route('/recommend', methods=['POST'])
# def recommend():
#     """
#     The main recommendation endpoint.
#     Expects a JSON payload with 'user_id', 'basket_ids', and 'gamma'.
#     """
#     # Get request data
#     data = request.get_json()
#     user_id = data.get('user_id')
#     basket_ids = data.get('basket_ids', [])
#     gamma = data.get('gamma', 0.5)

#     if user_id is None:
#         return jsonify({"error": "user_id is required"}), 400

#     try:
#         # --- The core ML logic, as explained previously ---
        
#         # 1. Construct Query Vector
#         user_vec = user_embeddings[user_id]
        
#         if not basket_ids:
#             query_vec = user_vec
#         else:
#             basket_vecs = [item_embeddings[pid] for pid in basket_ids if pid < len(item_embeddings)]
#             if not basket_vecs: # Handle case where all basket_ids are out of bounds
#                  query_vec = user_vec
#             else:
#                 avg_basket_vec = np.mean(basket_vecs, axis=0)
#                 query_vec = (user_vec + avg_basket_vec) / 2.0
        
#         faiss.normalize_L2(query_vec.reshape(1, -1))

#         # 2. Candidate Generation (FAISS)
#         _, candidate_indices = faiss_index.search(query_vec.reshape(1, -1).astype('float32'), k=N_CANDIDATES)
#         candidate_ids = candidate_indices[0]

#         # 3. Re-ranking
#         final_scores = []
#         for pid in candidate_ids:
#             if pid in basket_ids: continue

#             # Preference Score (dot product with normalized vectors is cosine similarity)
#             pref_score = np.dot(query_vec, item_embeddings[pid])
            
#             # Health Factor (lookup)
#             health_score = product_health_factors.get(pid, 0.5) # Default to 0.5 if not found

#             # Final Score
#             final_score = (1 - gamma) * pref_score + gamma * health_score
#             final_scores.append((int(pid), float(final_score)))
            
#         # 4. Sort and return top N product IDs
#         final_scores.sort(key=lambda x: x[1], reverse=True)
        
#         # Return only the product IDs
#         top_product_ids = [pid for pid, score in final_scores[:12]]

#         return jsonify({"recommendations": top_product_ids})

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return jsonify({"error": "Could not process the request."}), 500

# # --- 4. RUN THE APPLICATION ---
# if __name__ == '__main__':
#     load_artifacts() # Load models before starting the server
#     # Gunicorn is recommended for production instead of app.run()
#     app.run(host='0.0.0.0', port=5000, debug=True)

import os
import faiss
import numpy as np
import pandas as pd
import torch
import json
import traceback # Import traceback for detailed error logging

from flask import Flask, request, jsonify
from model import Triple2Vec # Import the model class

# --- 1. INITIALIZATION ---
print("Initializing Flask ML Service...")
app = Flask(__name__)

# --- 2. LOAD ML ARTIFACTS ON STARTUP ---
MODEL_DIR = 'ml_models'
N_CANDIDATES = 100

# --- Global variables for loaded artifacts ---
faiss_index = None
user_embeddings = None
item_embeddings = None
product_health_factors = None
prod2idx = None
idx2prod = None
# user2idx = None # If you add user mapping later

def load_artifacts():
    global faiss_index, user_embeddings, item_embeddings, product_health_factors, prod2idx, idx2prod #, user2idx

    # Load FAISS index
    faiss_index_path = os.path.join(MODEL_DIR, 'faiss_item_index.idx')
    try:
        print(f"Loading FAISS index from {faiss_index_path}...")
        faiss_index = faiss.read_index(faiss_index_path)
    except Exception as e:
        print(f"❌ Error loading FAISS index: {e}")
        exit()

    # Load the trained Triple2Vec model weights
    model_path = os.path.join(MODEL_DIR, 'triple2vec_model.pth')
    print(f"Loading model weights from {model_path}...")

    # --- Parameters from your training script ---
    num_users = 206209
    num_products = 10000
    embedding_dim = 64
    # ------------------------------------------

    model = Triple2Vec(num_users, num_products, embedding_dim)
    try:
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
    except FileNotFoundError:
        print(f"❌ Error: Model file not found at '{model_path}'.")
        exit()
    except RuntimeError as e:
        print(f"❌ Error loading model state dict: {e}")
        print("   Ensure the .pth file exists and model parameters (U, V, D) above match training.")
        exit()
    except Exception as e:
        print(f"❌ An unexpected error occurred loading the model: {e}")
        exit()

    # Extract embeddings
    try:
        user_embeddings = model.h.weight.data.cpu().numpy()
        item_p = model.p.weight.data.cpu().numpy()
        item_q = model.q.weight.data.cpu().numpy()
        item_embeddings = (item_p + item_q) / 2.0
        faiss.normalize_L2(item_embeddings)
        print(f"Embeddings loaded and combined. Shape: {item_embeddings.shape}")
    except Exception as e:
        print(f"❌ Error extracting embeddings from model: {e}")
        exit()


    # Load product health factor data
    nutrition_path = os.path.join(MODEL_DIR, 'products_with_nutrition_and_health_10k.parquet')
    try:
        print(f"Loading product health data from {nutrition_path}...")
        product_df = pd.read_parquet(nutrition_path)
        # --- FIXED Column Name ---
        # Use 'instacart_product' as identified by your inspection script
        product_health_factors = dict(zip(product_df['instacart_product'], product_df['health_factor']))
        # -------------------------
    except FileNotFoundError:
         print(f"❌ Error: Product data file not found at '{nutrition_path}'.")
         exit()
    except KeyError as ke:
         print(f"❌ Error loading product data: Missing expected column '{ke}'.")
         print(f"   Available columns: {list(product_df.columns)}")
         print("   Please ensure the Parquet file has the correct column names ('instacart_product', 'health_factor_score').")
         exit()
    except Exception as e:
        print(f"❌ Error loading product data: {e}")
        exit()

    # Load Product ID to Index Mapping
    prod2idx_path = os.path.join(MODEL_DIR, 'product_to_idx.json') # Ensure filename matches training script
    try:
        with open(prod2idx_path, 'r') as f:
            prod2idx_str_keys = json.load(f)
            prod2idx = {int(k): v for k, v in prod2idx_str_keys.items()}
        idx2prod = {v: k for k, v in prod2idx.items()}
        print(f"✅ Loaded product ID <-> index mappings ({len(prod2idx)} entries).")
         # Sanity Check
        if len(prod2idx) != num_products:
             print(f"⚠️ Warning: Mismatch between num_products ({num_products}) and mapping size ({len(prod2idx)}).")
        if item_embeddings.shape[0] != num_products:
             print(f"⚠️ Warning: Mismatch between num_products ({num_products}) and item embedding rows ({item_embeddings.shape[0]}).")

    except FileNotFoundError:
        print(f"❌ Error: Product mapping file not found at '{prod2idx_path}'. Cannot run server.")
        exit()
    except Exception as e:
        print(f"❌ Error loading product mapping: {e}")
        exit()

    # --- TODO: Load user2idx mapping if available ---

    print("✅ ML artifacts loaded successfully.")

# --- 3. DEFINE THE RECOMMENDATION API ENDPOINT ---
@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    original_user_id = data.get('user_id') # This may be None
    original_basket_ids = data.get('basket_ids', [])
    gamma = data.get('gamma', 0.5)

    try:
        user_vec = None

        # --- (FIXED) NEW USER LOGIC ---
        if original_user_id is not None:
            # This is an EXISTING user. Find their embedding vector.
            # TODO: Add your user2idx.json mapping logic here
            user_index = original_user_id # Assuming ID is index for now
            
            if user_index >= 0 and user_index < len(user_embeddings):
                user_vec = user_embeddings[user_index]
            else:
                print(f"Warning: Existing user ID {original_user_id} not found. Treating as new user.")
        # If original_user_id is None, user_vec remains None
        # --- (END OF FIX) ---

        # Convert basket IDs to indices
        basket_indices = [prod2idx.get(pid) for pid in original_basket_ids if prod2idx.get(pid) is not None]

        # 1. Construct Query Vector
        if user_vec is not None:
            # --- LOGIC FOR EXISTING USER ---
            if not basket_indices:
                query_vec = user_vec # No basket, use user history
            else:
                # Has history AND basket, combine them
                basket_vecs = [item_embeddings[idx] for idx in basket_indices]
                avg_basket_vec = np.mean(basket_vecs, axis=0)
                query_vec = (user_vec + avg_basket_vec) / 2.0
        else:
            # --- LOGIC FOR NEW USER ---
            if not basket_indices:
                # New user AND empty basket. Node.js should have caught this,
                # but we'll return an empty list just in case.
                print("[Flask] Received request for new user with empty basket. Returning empty.")
                return jsonify({"recommendations": []})
            else:
                # New user, but has items in basket. Use basket ONLY.
                print(f"[Flask] New user request. Using session-based recs for {len(basket_indices)} items.")
                basket_vecs = [item_embeddings[idx] for idx in basket_indices]
                avg_basket_vec = np.mean(basket_vecs, axis=0)
                query_vec = avg_basket_vec # Query is *only* the basket
        
        # --- (Rest of the function is the same) ---

        query_vec_norm = query_vec.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_vec_norm)

        # 2. Candidate Generation (FAISS returns INDICES)
        try:
            _, candidate_indices = faiss_index.search(query_vec_norm, k=N_CANDIDATES)
            candidate_indices = candidate_indices[0] 
        except Exception as faiss_e:
             print(f"Error during FAISS search: {faiss_e}")
             return jsonify({"error": "Failed during candidate search."}), 500

        # 3. Re-ranking using INDICES
        final_scores = []
        for idx in candidate_indices:
            idx = int(idx)
            if idx < 0 or idx >= len(item_embeddings): continue
            if idx in basket_indices: continue

            original_pid = idx2prod.get(idx)
            if original_pid is None: continue

            pref_score = np.dot(query_vec_norm[0], item_embeddings[idx])
            health_score = product_health_factors.get(original_pid, 0.5) 
            final_score = (1 - gamma) * pref_score + gamma * health_score
            final_scores.append((original_pid, float(final_score)))

        # 4. Sort and return top N ORIGINAL product IDs
        final_scores.sort(key=lambda x: x[1], reverse=True)
        top_original_product_ids = [pid for pid, score in final_scores[:12]]

        return jsonify({"recommendations": top_original_product_ids})

    except Exception as e:
        print(f"An unexpected error occurred during recommendation: {e}")
        traceback.print_exc()
        return jsonify({"error": "Could not process the request."}), 500

# --- 4. RUN THE APPLICATION ---
if __name__ == '__main__':
    load_artifacts()
    print(f"✅ Flask server starting on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)