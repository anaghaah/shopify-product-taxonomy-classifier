# 🛍️ Shopify Product Taxonomy Auto-Classifier & Intelligence Suite

An automated, fault-tolerant classification and attribute extraction engine designed to map extensive e-commerce catalogs (10,000+ SKUs) directly to standard **Shopify Product Taxonomy categories**.

Built with a high-performance **FastAPI** backend, vector-space NLP classification, and a modern, SaaS-grade human-in-the-loop verification dashboard.

---

## 🚀 Key Features

* **Automated Taxonomy Categorization:** Leverages TF-IDF vectorization and Cosine Similarity to map raw product titles, descriptions, and vendor data against 14,600+ official Shopify taxonomy categories.
* **Confidence Scoring & Alternatives:** Generates normalized confidence scores for every prediction, automatically proposing Top-2 fallback alternatives for items scoring below 35%.
* **Attribute & Value Extraction:** Accurately extracts colors, materials (Leather, Velvet, Wood, Steel), apparel sizes, and dimensional specifications directly from product metadata.
* **Resilient Batch Processing:** Fault-tolerant background pipeline that processes catalogs in 100-item chunks. Fully supports pause-and-resume without re-processing completed records.
* **Human-in-the-Loop Review Dashboard:** Modern interactive dashboard featuring live catalog search, low-confidence review filtering, one-click approvals, and modal-based category overrides.

---

## 🛠️ Architecture & Tech Stack

* **Backend Framework:** FastAPI (Asynchronous Python 3)
* **Classifier Engine:** Scikit-learn (TF-IDF Vectorizer, Cosine Similarity)
* **Data Persistence:** SQLite (Lightweight, robust relational store)
* **Data Ingestion:** Pandas, OpenPyXL
* **Frontend:** Modern HTML5 / CSS3 / JavaScript (Shopify Polaris & Tailwind-inspired design)

---

## 📦 Local Installation & Setup

Follow these steps to run the application locally:

### 1. Clone the Repository
```bash
git clone https://github.com/anaghaah/shopify-product-taxonomy-classifier.git
cd shopify-product-taxonomy-classifier