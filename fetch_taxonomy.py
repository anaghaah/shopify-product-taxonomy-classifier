import json
import urllib.request

TAXONOMY_URL = "https://raw.githubusercontent.com/shopify/product-taxonomy/main/dist/en/categories.txt"

def fetch_and_save():
    print("Downloading Shopify Taxonomy...")
    req = urllib.request.Request(TAXONOMY_URL, headers={'User-Agent': 'Mozilla/5.0'})
    
    categories = []
    with urllib.request.urlopen(req) as response:
        lines = response.read().decode('utf-8').splitlines()
        for line in lines:
            line = line.strip()
            
            if line and not line.startswith('#'):
                categories.append(line)
                
    with open("taxonomy.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2)
        
    print(f"Successfully downloaded! {len(categories)} categories saved to taxonomy.json.")

if __name__ == "__main__":
    fetch_and_save()