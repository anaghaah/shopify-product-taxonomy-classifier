import sqlite3
import pandas as pd
import json
from engine import TaxonomyEngine

engine = TaxonomyEngine()
excel_file = "Product List.xlsx"

df = pd.read_excel(excel_file).fillna("")

conn = sqlite3.connect("products.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_number TEXT UNIQUE,
    title TEXT,
    description TEXT,
    brand TEXT,
    product_type TEXT,
    image_url TEXT,
    predicted_category TEXT,
    confidence REAL,
    alternative_suggestions TEXT,
    attributes TEXT,
    needs_review INTEGER,
    approved INTEGER DEFAULT 0
)
""")

for _, row in df.iterrows():
    p_num = str(row.get("Product Number", "")).strip()
    title = str(row.get("Product Name", "")).strip()
    desc = str(row.get("Product Description", "")).strip()
    brand = str(row.get("Collection Name", "")).strip() or "Modway"
    p_type = str(row.get("Product Category", "")).strip()
    img = str(row.get("Image 1", "")).strip()

    # Combined feature context (Requirement 6)
    feature_text = f"{title} {p_type} {brand} {desc}"

    # Classification & Attributes
    pred_cat, score, alts, needs_rev = engine.classify(feature_text)
    attrs = engine.extract_attributes(row)

    cursor.execute("""
    INSERT OR REPLACE INTO products 
    (product_number, title, description, brand, product_type, image_url, predicted_category, confidence, alternative_suggestions, attributes, needs_review, approved)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        p_num, title, desc, brand, p_type, img, pred_cat, score,
        json.dumps(alts), json.dumps(attrs), needs_rev
    ))

conn.commit()
conn.close()
print("Catalog processed with complete multi-field feature context.")