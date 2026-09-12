import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TaxonomyEngine:
    def __init__(self, taxonomy_file="taxonomy.json"):
        with open(taxonomy_file, "r", encoding="utf-8") as f:
            self.categories = json.load(f)
        
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.category_vectors = self.vectorizer.fit_transform(self.categories)

    def classify(self, text, threshold=0.35):
        if not text.strip():
            return "Uncategorized", 0.0, ["General Merchandise"], 1

        query_vec = self.vectorizer.transform([text])
        similarities = cosine_similarity(query_vec, self.category_vectors).flatten()
        
        top_indices = similarities.argsort()[::-1][:3]
        best_category = self.categories[top_indices[0]]
        best_score = float(similarities[top_indices[0]])
        
        alternatives = [self.categories[i] for i in top_indices[1:3]]
        needs_review = 1 if best_score < threshold else 0
        
        return best_category, round(best_score, 4), alternatives, needs_review

    def extract_attributes(self, row):
        text = f"{row.get('Product Name', '')} {row.get('Product Description', '')} {row.get('Product Category', '')}"
        
        # Color
        color = str(row.get("Product Color", "")).strip()
        if not color or color.lower() == "nan":
            found_color = re.findall(r"\b(White|Black|Blue|Gray|Brown|Red|Green|Gold|Silver|Beige)\b", text, re.I)
            color = found_color[0].capitalize() if found_color else "Unspecified"

        # Material
        material = str(row.get("Materials", "")).strip()
        if not material or material.lower() == "nan":
            found_mat = re.findall(r"\b(Leather|Fabric|Wood|Metal|Steel|Glass|Plastic|Velvet|Chrome)\b", text, re.I)
            material = found_mat[0].capitalize() if found_mat else "Unspecified"

        # Dimensions & Weight
        dimensions = str(row.get("Product Dimensions", "")).strip()
        if not dimensions or dimensions.lower() == "nan":
            dim_match = re.search(r"\d+(\.\d+)?\s*[\"xX×lLwWhH]+\s*\d+(\.\d+)?", text)
            dimensions = dim_match.group(0) if dim_match else "N/A"

        weight = str(row.get("Product Weight", "")).strip()
        if not weight or weight.lower() == "nan":
            weight = "N/A"

        return {
            "color": color,
            "material": material,
            "dimensions": dimensions,
            "weight": weight
        }