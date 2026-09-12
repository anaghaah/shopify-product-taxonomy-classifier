# Shopify Product Taxonomy Auto-Classifier

An automated system designed to classify large e-commerce product catalogs (10,000+ items) into official Shopify Taxonomy categories and extract product attributes.

---

### 1. What Was Built
* **Automated Product Classification:** Maps product titles, descriptions, and categories to the official Shopify Product Taxonomy (14,600+ categories).
* **Confidence Scoring & Alternatives:** Generates confidence scores for every prediction and provides fallback alternative suggestions when confidence is low.
* **Attribute Extraction:** Automatically extracts key attributes such as Material, Color, Dimensions, and Apparel sizes from raw metadata.
* **Fault-Tolerant Batch Pipeline:** Ingests catalogs in batches, handling missing descriptions, invalid fields, and network issues gracefully without stopping.
* **Review Dashboard:** A web dashboard allowing merchants to view results, filter low-confidence items, edit categories, and approve predictions.

---

### 2. How It Works
1. **Taxonomy Ingestion:** Fetches official Shopify taxonomy categories and builds an indexed catalog.
2. **Text Processing & Vector Matching:** Combines title, product type, vendor, and description, converts them into TF-IDF vector representations, and calculates Cosine Similarity against all taxonomy categories.
3. **Thresholding & Review Queue:** Predictions scoring below 0.35 confidence are flagged for manual review and provided with secondary category options.
4. **Database & API:** Stores results in a relational SQLite database and exposes REST APIs for searching, updating, and approving products.

---

### 3. Tech Stack Used
* **Backend:** Python 3, FastAPI, Uvicorn
* **Data Processing & ML:** Scikit-learn (TF-IDF, Cosine Similarity), Pandas, OpenPyXL
* **Database:** SQLite
* **Frontend:** HTML5, CSS3, JavaScript (Clean UI with Approve/Edit review workflows)
* **Deployment:** Render
