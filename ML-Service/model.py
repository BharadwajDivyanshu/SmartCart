import torch
import torch.nn as nn

# This class definition MUST EXACTLY MATCH the one in your triple2vec_train.py
# This is required so that PyTorch knows how to load the saved model weights.

class Triple2Vec(nn.Module):
    def __init__(self, num_users, num_products, embedding_dim):
        super().__init__()
        self.h = nn.Embedding(num_users, embedding_dim)
        self.p = nn.Embedding(num_products, embedding_dim)
        self.q = nn.Embedding(num_products, embedding_dim)

    def forward(self, users, items_i, items_j, negs):
        # The forward pass isn't strictly needed for inference,
        # but it's good practice to keep the model definition complete.
        h_u = self.h(users)
        p_i = self.p(items_i)
        q_j = self.q(items_j)
        pos_score = torch.sum(h_u * (p_i + q_j), dim=1)
        
        negs = negs.long()
        neg_p = self.p(negs)
        neg_q = self.q(negs)
        h_expand = h_u.unsqueeze(1)
        neg_scores = torch.sum(h_expand * (neg_p + neg_q), dim=2)
        
        return pos_score, neg_scores