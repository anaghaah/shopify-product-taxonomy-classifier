import sqlite3
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_NAME = "products.db"

def init_db():
    """Initializes the database schema for product categorization tracking."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT,
        title TEXT,
        description TEXT,
        brand TEXT,
        image_url TEXT,
        predicted_category TEXT,
        confidence_score REAL,
        alt_category_1 TEXT,
        alt_category_2 TEXT,
        attributes TEXT,
        status TEXT DEFAULT 'PENDING',
        manual_review INTEGER DEFAULT 0,
        approved INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

class TaxonomyClassifier:
    def __init__(self, taxonomy_path="taxonomy.json"):
        with open(taxonomy_path, "r", encoding="utf-8") as f:
            self.categories = json.load(f)
        
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=20000)
        self.taxonomy_matrix = self.vectorizer.fit_transform(self.categories)

    def extract_attributes(self, text):
        """
        Extracts comprehensive e-commerce attributes:
        Colors, Sizes, Dimensions, and Materials.
        """
        attrs = {}
        lower_text = text.lower()

        # 1. Colors
        colors = [
            'red', 'blue', 'green', 'black', 'white', 'yellow', 'grey', 'gray',
            'pink', 'brown', 'navy', 'gold', 'silver', 'beige', 'charcoal', 'walnut'
        ]
        for c in colors:
            if re.search(rf"\b{c}\b", lower_text):
                attrs['color'] = c.capitalize()
                break

        # 2. Materials
        materials = [
            'leather', 'velvet', 'wood', 'teak', 'marble', 'steel', 
            'stainless steel', 'fabric', 'metal', 'glass', 'cotton', 'mesh'
        ]
        for m in materials:
            if re.search(rf"\b{m}\b", lower_text):
                attrs['material'] = m.title()
                break

        # 3. Sizes (Standard apparel sizes)
        sizes = ['xs', 's', 'm', 'l', 'xl', 'xxl', 'small', 'medium', 'large']
        for s in sizes:
            if re.search(rf"\b{s}\b", lower_text):
                attrs['size'] = s.upper()
                break

        # 4. Dimensions / Furniture sizes (e.g., 48", 54", 60", 72-inch)
        dimension_match = re.search(r'(\d+)\s*(?:\"|\s*inch|\s*in\b)', lower_text)
        if dimension_match:
            attrs['dimension'] = f"{dimension_match.group(1)}\""

        return attrs

    def classify(self, title, description="", brand=""):
        combined_text = f"{title or ''} {description or ''} {brand or ''}".strip()
        if not combined_text:
            return "Uncategorized", 0.0, [], {}

        query_vec = self.vectorizer.transform([combined_text])
        sim_scores = cosine_similarity(query_vec, self.taxonomy_matrix).flatten()
        
        top_indices = sim_scores.argsort()[-3:][::-1]
        top_scores = [float(sim_scores[i]) for i in top_indices]
        top_categories = [self.categories[i] for i in top_indices]

        confidence = round(top_scores[0] * 100, 2)
        attributes = self.extract_attributes(combined_text)
        
        return top_categories[0], confidence, top_categories[1:], attributes