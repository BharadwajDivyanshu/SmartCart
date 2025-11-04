# import pandas as pd

# # Full path to your file
# file_path = "data/openfoodfacts/en.openfoodfacts.org.products.csv"

# # Preview first few rows safely
# df = pd.read_csv(
#     file_path,
#     sep="\t",             # Use tab separator
#     nrows=5,              # Preview first 5 rows
#     low_memory=False,
#     on_bad_lines='skip'   # Skip malformed rows
# )

# print(df.columns.tolist())  # Check actual column names
# print(df.head())
# import pandas as pd

# # Path to your OpenFoodFacts CSV
# file_path = "data/products_with_nutrition_and_health_10k.parquet"

# # Load only the header (very fast even for huge files)
# df = pd.read_parquet(file_path, sep='\t', nrows=0, low_memory=False)

# # Number of columns
# num_columns = len(df.columns)
# print(f"Number of columns: {num_columns}\n")

# # List of all column names
# print("Column names:")
# for col in df.columns:
#     print(col)

import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)

# Path to your Parquet file
file_path = "../ml_models/products_with_nutrition_and_health_10k.parquet"

# Load the file metadata first (optional, but safe)
df = pd.read_parquet(file_path, columns=None)

# Print total columns
print(f"Total columns in file: {len(df)}\n")

# Print the first 5 column names
print("All columns:")
# Just remove the [:5] slice to loop through all columns
for col in df.columns:
    print(col)

# Optional: show first few rows of those 5 columns
print("\nPreview of these columns:")
print(df[df.columns[:5]].head())
