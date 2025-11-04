# usda_fetch.py
import requests, time, os, json
API_KEY = "YOUR_USDA_API_KEY"  # get from https://fdc.nal.usda.gov/api-key-signup
outdir = "data/usda"
os.makedirs(outdir, exist_ok=True)

# Example: search endpoint for "brown rice"
def search_food(query, page=1):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key":API_KEY,"query":query,"pageSize":25,"pageNumber":page}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

res = search_food("brown rice")
with open(os.path.join(outdir,"brown_rice_search.json"),"w") as f:
    json.dump(res,f,indent=2)
print("Saved example USDA search result.")
