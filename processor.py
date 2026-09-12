import sqlite3
import json
import time
import pandas as pd
from engine import init_db, TaxonomyClassifier, DB_NAME

def import_from_excel(file_path="Product List.xlsx"):
    """
    Reads catalog and inserts records with PENDING status in efficient chunks.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"Reading catalog from {file_path}...")
    df = pd.read_excel(file_path)

    cols = {str(c).lower().strip(): c for c in df.columns}
    title_col = cols.get('title', cols.get('product name', cols.get('name', None)))
    desc_col = cols.get('description', cols.get('body (html)', cols.get('desc', None)))
    brand_col = cols.get('brand', cols.get('vendor', None))
    img_col = cols.get('image', cols.get('image_url', cols.get('images', cols.get('image src', None))))

    inserted_count = 0
    records = []
    for _, row in df.iterrows():
        title = str(row[title_col]) if title_col and pd.notna(row[title_col]) else ""
        desc = str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else ""
        brand = str(row[brand_col]) if brand_col and pd.notna(row[brand_col]) else ""
        img = str(row[img_col]) if img_col and pd.notna(row[img_col]) else ""

        if not title and not desc:
            continue

        records.append((title, desc, brand, img, 'PENDING'))
        inserted_count += 1

    cursor.executemany("""
        INSERT INTO products (title, description, brand, image_url, status)
        VALUES (?, ?, ?, ?, ?)
    """, records)

    conn.commit()
    conn.close()
    print(f"Ingested {inserted_count} products ready for batch processing.")

def process_pending_batch(classifier, batch_size=100):
    """
    Pulls a isolated batch of PENDING records, performs classification,
    and updates their status atomically.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, description, brand 
        FROM products 
        WHERE status = 'PENDING' 
        LIMIT ?
    """, (batch_size,))
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return 0

    processed_count = 0
    for pid, title, desc, brand in rows:
        try:
            pred_cat, confidence, alts, attrs = classifier.classify(title, desc, brand)
            manual_review = 1 if confidence < 35.0 else 0
            alt1 = alts[0] if len(alts) > 0 else ""
            alt2 = alts[1] if len(alts) > 1 else ""

            cursor.execute("""
                UPDATE products 
                SET predicted_category = ?, 
                    confidence_score = ?, 
                    alt_category_1 = ?, 
                    alt_category_2 = ?, 
                    attributes = ?, 
                    status = 'COMPLETED', 
                    manual_review = ? 
                WHERE id = ?
            """, (pred_cat, confidence, alt1, alt2, json.dumps(attrs), manual_review, pid))
            processed_count += 1

        except Exception as err:
            print(f"Error processing item ID {pid}: {err}")
            cursor.execute("UPDATE products SET status = 'FAILED' WHERE id = ?", (pid,))

    conn.commit()
    conn.close()
    return processed_count

def run_production_worker(batch_size=100, max_items=15000):
    """
    Continuous background loop that processes products in batches of 100.
    Handles 10,000+ products smoothly without memory leaks or crashing.
    """
    print("Loading Shopify Taxonomy into memory...")
    classifier = TaxonomyClassifier()
    total_processed = 0

    print(f"Starting batch worker (Chunk size: {batch_size})...")
    start_time = time.time()

    while total_processed < max_items:
        processed_in_batch = process_pending_batch(classifier, batch_size=batch_size)
        if processed_in_batch == 0:
            print("All pending products processed! Worker complete.")
            break

        total_processed += processed_in_batch
        print(f"Progress: {total_processed} products classified...")

    duration = round(time.time() - start_time, 2)
    print(f"Completed processing {total_processed} products in {duration} seconds.")

if __name__ == "__main__":
    # Runs the resilient batch worker loop
    run_production_worker(batch_size=100)