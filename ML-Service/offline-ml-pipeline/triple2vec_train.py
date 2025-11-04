import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
from tqdm import tqdm
import random
import numpy as np
import json
import os

# ---------------- CONFIG ---------------- #
EMBED_DIM = 64
BATCH = 512
EPOCHS = 4
NEG_SAMPLES = 5
LR = 0.001
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_PRODUCTS = 10000  # Use a subset for faster prototyping

# --- Output Files ---
OUTPUT_DIR = "data/embeddings"
MODEL_FILE = os.path.join(OUTPUT_DIR, "triple2vec_model.pth")
EMBEDDINGS_FILE = os.path.join(OUTPUT_DIR, "product_embeddings.npy")
PROD2IDX_FILE = os.path.join(OUTPUT_DIR, "product_to_idx.json")
# --------------------------- #

print(f"Using device: {DEVICE}")

# Load data
try:
    orders = pd.read_csv("data/kaggle/order_products__prior.csv")
    orders_meta = pd.read_csv("data/kaggle/orders.csv")
    products = pd.read_csv("data/kaggle/products.csv")[:MAX_PRODUCTS]
except FileNotFoundError as e:
    print(f"❌ Error loading data: {e}")
    print("Please ensure the Kaggle Instacart data is in the 'data/kaggle/' directory.")
    exit()


orders = orders.merge(orders_meta[['order_id','user_id']], on='order_id', how='left')

# Build mappings
prod2idx = {int(p):i for i,p in enumerate(products['product_id'].tolist())}
user2idx = {int(u):i for i,u in enumerate(orders_meta['user_id'].unique().tolist())}

V = len(prod2idx)
U = len(user2idx)
print(f"Vocab sizes: Products={V}, Users={U}")

# Rebuild baskets per order (only products in the subset)
print("Grouping orders into baskets...")
orders_grouped = orders.groupby('order_id').agg({'user_id':'first','product_id': lambda x: [int(p) for p in x if int(p) in prod2idx]}).reset_index()
orders_grouped = orders_grouped[orders_grouped['product_id'].map(len) > 1].reset_index(drop=True)
print(f"Created {len(orders_grouped)} baskets for training.")

# ---------------- Dataset ---------------- #
class TripleDataset(Dataset):
    def __init__(self, orders_grouped, user2idx, prod2idx, neg_k=5):
        self.orders_grouped = orders_grouped
        self.user2idx = user2idx
        self.prod2idx = prod2idx
        self.neg_k = neg_k
        self.V = len(prod2idx)

    def __len__(self):
        return len(self.orders_grouped)

    def __getitem__(self, idx):
        row = self.orders_grouped.iloc[idx]
        u = self.user2idx[int(row['user_id'])]
        items = row['product_id']
        # Pick two distinct products from the basket
        i, j = random.sample(items, 2)
        i_idx, j_idx = self.prod2idx[i], self.prod2idx[j]
        # Generate negative samples (random products not in the positive pair)
        negs = []
        while len(negs) < self.neg_k:
            n = random.randint(0, self.V-1)
            if n != i_idx and n != j_idx:
                negs.append(n)
        return torch.tensor(u), torch.tensor(i_idx), torch.tensor(j_idx), torch.tensor(negs)

dataset = TripleDataset(orders_grouped, user2idx, prod2idx, NEG_SAMPLES)
loader = DataLoader(dataset, batch_size=BATCH, shuffle=True, num_workers=0) # num_workers=0 for Windows/macOS compatibility

# ---------------- Model ---------------- #
class Triple2Vec(nn.Module):
    def __init__(self, U, V, D):
        super().__init__()
        self.h = nn.Embedding(U, D) # User embeddings
        self.p = nn.Embedding(V, D) # Product "context" embeddings
        self.q = nn.Embedding(V, D) # Product "center" embeddings

    def forward(self, users, items_i, items_j, negs):
        h_u = self.h(users)
        p_i = self.p(items_i)
        q_j = self.q(items_j)
        pos_score = (h_u * (p_i + q_j)).sum(dim=1)

        neg_p = self.p(negs)
        neg_q = self.q(negs)
        neg_scores = (h_u.unsqueeze(1) * (neg_p + neg_q)).sum(dim=2)
        return pos_score, neg_scores

model = Triple2Vec(U, V, EMBED_DIM).to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=LR)
bce = nn.BCEWithLogitsLoss(reduction='none')

# ---------------- Training ---------------- #
print("\n🔥 Starting model training...")
for epoch in range(EPOCHS):
    total_loss = 0.0
    # Use tqdm for a nice progress bar
    for users, i_idx, j_idx, negs in tqdm(loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        users, i_idx, j_idx, negs = users.to(DEVICE), i_idx.to(DEVICE), j_idx.to(DEVICE), negs.to(DEVICE)
        pos_score, neg_scores = model(users, i_idx, j_idx, negs)

        pos_loss = bce(pos_score, torch.ones_like(pos_score))
        neg_loss = bce(neg_scores, torch.zeros_like(neg_scores)).sum(dim=1)
        loss = (pos_loss + neg_loss).mean()

        opt.zero_grad()
        loss.backward()
        opt.step()
        total_loss += loss.item()
    print(f"Epoch {epoch+1}/{EPOCHS} -> Average Loss: {total_loss/len(loader):.4f}")

print("✅ Training complete.")

# ---------------- Save Model and Embeddings (NEW SECTION) ---------------- #
print("\n💾 Saving model and embeddings...")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Save the model state dictionary (the .pth file)
torch.save(model.state_dict(), MODEL_FILE)
print(f"   - Model state saved to: {MODEL_FILE}")

# 2. Extract, combine, and save the product embeddings
# We combine p and q embeddings (common practice) to get a single vector per product
p_embed = model.p.weight.detach().cpu().numpy()
q_embed = model.q.weight.detach().cpu().numpy()
product_embeddings = (p_embed + q_embed) / 2.0

np.save(EMBEDDINGS_FILE, product_embeddings)
print(f"   - Product embeddings (.npy) saved to: {EMBEDDINGS_FILE}")

# 3. Save the product_id -> index mapping (CRITICAL for using the embeddings)
with open(PROD2IDX_FILE, 'w') as f:
    json.dump(prod2idx, f)
print(f"   - Product-to-index mapping (.json) saved to: {PROD2IDX_FILE}")

print("\n🎉 All done!")