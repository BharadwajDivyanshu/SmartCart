# compute_health_factor.py
import pandas as pd
import numpy as np

# Define ideal per-100g macros (this is example; adjust to WHO/custom profile)
ideal = {"protein":10.0,"fat":10.0,"carbs":30.0}  # grams per 100g, example

def compute_hf(nutriments):
    # nutriments: dict from OpenFoodFacts, might contain 'proteins_100g','fat_100g','carbohydrates_100g'
    p = nutriments.get('proteins_100g') or 0.0
    f = nutriments.get('fat_100g') or 0.0
    c = nutriments.get('carbohydrates_100g') or 0.0
    # normalized deviation (L2)
    dev = np.sqrt((p-ideal['protein'])**2 + (f-ideal['fat'])**2 + (c-ideal['carbs'])**2)
    # convert to score in [0,1] where smaller dev => higher HF
    max_dev = 100.0
    hf = max(0.0, 1.0 - dev / max_dev)
    return hf