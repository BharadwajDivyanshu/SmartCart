# download_kaggle.py
import os, subprocess, sys

datasets = [
    "psparks/instacart-market-basket-analysis",
    "chiranjivdas09/ta-feng-grocery-dataset",
    "saldenisov/recipenlg"
]

outdir = "data/kaggle"
os.makedirs(outdir, exist_ok=True)

for ds in datasets:
    print("Downloading", ds)
    subprocess.run(["kaggle", "datasets", "download", "-d", ds, "-p", outdir, "--unzip"], check=True)
print("Done. Files saved to", outdir)