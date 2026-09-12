from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import json

app = FastAPI(title="Shopify Product Taxonomy Classifier")
DB_NAME = "products.db"

class UpdateCategoryRequest(BaseModel):
    category: str

@app.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'COMPLETED'")
    completed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'PENDING'")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products WHERE manual_review = 1")
    review = cursor.fetchone()[0]
    conn.close()
    return {"total": total, "completed": completed, "pending": pending, "review": review}

@app.get("/api/products")
def get_products(page: int = 1, page_size: int = 50, status: str = "ALL"):
    offset = (page - 1) * page_size
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if status == "ALL":
        cursor.execute("SELECT * FROM products WHERE status = 'COMPLETED' LIMIT ? OFFSET ?", (page_size, offset))
    elif status == "REVIEW":
        cursor.execute("SELECT * FROM products WHERE manual_review = 1 LIMIT ? OFFSET ?", (page_size, offset))
    else:
        cursor.execute("SELECT * FROM products WHERE status = ? LIMIT ? OFFSET ?", (status, page_size, offset))
        
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.post("/api/approve/{product_id}")
def approve_product(product_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET approved = 1, manual_review = 0 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "id": product_id}

@app.put("/api/update-category/{product_id}")
def update_category(product_id: int, payload: UpdateCategoryRequest):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products 
        SET predicted_category = ?, approved = 1, manual_review = 0 
        WHERE id = ?
    """, (payload.category, product_id))
    conn.commit()
    conn.close()
    return {"status": "success", "id": product_id, "new_category": payload.category}

@app.get("/", response_class=HTMLResponse)
def render_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shopify Taxonomy Classification Dashboard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 24px; background: #f1f5f9; color: #0f172a; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
            .stats-bar { display: flex; gap: 16px; margin-bottom: 20px; }
            .stat-card { background: white; padding: 12px 18px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); font-size: 13px; color: #64748b; }
            .stat-card strong { display: block; font-size: 20px; color: #0f172a; margin-top: 4px; }
            .filter-btn { padding: 8px 16px; margin-right: 8px; border: 1px solid #cbd5e1; background: white; border-radius: 6px; cursor: pointer; font-weight: 500; }
            .filter-btn.active { background: #0f172a; color: white; border-color: #0f172a; }
            .card { background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow-x: auto; }
            table { width: 100%; border-collapse: collapse; text-align: left; }
            th { background: #f8fafc; padding: 12px 16px; font-size: 13px; text-transform: uppercase; color: #64748b; border-bottom: 1px solid #e2e8f0; position: sticky; top: 0; }
            td { padding: 14px 16px; border-bottom: 1px solid #f1f5f9; font-size: 14px; vertical-align: top; }
            .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }
            .high { background: #dcfce7; color: #166534; }
            .low { background: #fee2e2; color: #991b1b; }
            .btn-approve { background: #16a34a; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }
            .btn-edit { background: #2563eb; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 4px; }
            .review-warning { color: #dc2626; font-size: 11px; font-weight: bold; display: block; margin-top: 4px; }
            .category-path { color: #0284c7; font-weight: 600; font-size: 13px; }
            .alts { font-size: 12px; color: #64748b; margin-top: 6px; background: #f8fafc; padding: 6px; border-radius: 4px; border: 1px solid #e2e8f0; }
            .pagination { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: white; border-top: 1px solid #e2e8f0; border-radius: 0 0 8px 8px; }
            .page-btn { padding: 6px 14px; border: 1px solid #cbd5e1; background: white; border-radius: 4px; cursor: pointer; }
            .page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
            .attr-pill { display: inline-block; background: #e2e8f0; color: #334155; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin: 2px; font-weight: 500; }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h2 style="margin:0;">Shopify Taxonomy Auto-Classifier</h2>
                <small style="color: #64748b;">Batch review and confidence verification interface</small>
            </div>
            <div>
                <button class="filter-btn active" onclick="setFilter('ALL', this)">All Completed</button>
                <button class="filter-btn" onclick="setFilter('REVIEW', this)">Needs Review (<35%)</button>
            </div>
        </div>

        <div class="stats-bar" id="stats-container">
            <div class="stat-card">Total Products<strong id="stat-total">-</strong></div>
            <div class="stat-card">Categorized<strong id="stat-completed" style="color:#16a34a;">-</strong></div>
            <div class="stat-card">Pending<strong id="stat-pending" style="color:#d97706;">-</strong></div>
            <div class="stat-card">Requires Review<strong id="stat-review" style="color:#dc2626;">-</strong></div>
        </div>

        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">ID</th>
                        <th style="width: 320px;">Product Title & Brand</th>
                        <th>Predicted Category & Alternatives</th>
                        <th style="width: 100px;">Confidence</th>
                        <th style="width: 150px;">Attributes</th>
                        <th style="width: 170px;">Action</th>
                    </tr>
                </thead>
                <tbody id="rows">
                    <tr><td colspan="6" style="text-align:center;">Loading products...</td></tr>
                </tbody>
            </table>
            <div class="pagination">
                <button class="page-btn" id="prev-btn" onclick="changePage(-1)">Previous</button>
                <span id="page-info" style="font-size: 14px; color: #64748b;">Page 1</span>
                <button class="page-btn" id="next-btn" onclick="changePage(1)">Next</button>
            </div>
        </div>

        <script>
            let currentPage = 1;
            let currentFilter = 'ALL';
            const pageSize = 50;

            function cleanCategory(text) {
                if (!text) return 'N/A';
                if (text.includes(' : ')) return text.split(' : ')[1].trim();
                return text;
            }

            function formatAttributes(attrString) {
                if (!attrString) return '<span style="color:#94a3b8;">—</span>';
                try {
                    const parsed = JSON.parse(attrString);
                    const keys = Object.keys(parsed);
                    if (keys.length === 0) return '<span style="color:#94a3b8;">—</span>';
                    return keys.map(k => `<span class="attr-pill">${k}: <strong>${parsed[k]}</strong></span>`).join(' ');
                } catch(e) {
                    return '<span style="color:#94a3b8;">—</span>';
                }
            }

            async function loadStats() {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stat-total').innerText = data.total;
                document.getElementById('stat-completed').innerText = data.completed;
                document.getElementById('stat-pending').innerText = data.pending;
                document.getElementById('stat-review').innerText = data.review;
            }

            async function loadTable() {
                const res = await fetch(`/api/products?page=${currentPage}&page_size=${pageSize}&status=${currentFilter}`);
                const data = await res.json();
                const tbody = document.getElementById('rows');

                document.getElementById('page-info').innerText = `Page ${currentPage}`;
                document.getElementById('prev-btn').disabled = (currentPage === 1);
                document.getElementById('next-btn').disabled = (data.length < pageSize);

                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 30px;">No records found.</td></tr>';
                    return;
                }

                tbody.innerHTML = data.map(p => {
                    const isLow = p.confidence_score < 35.0;
                    const cleanMain = cleanCategory(p.predicted_category);
                    const cleanAlt1 = cleanCategory(p.alt_category_1);
                    const cleanAlt2 = cleanCategory(p.alt_category_2);

                    return `
                        <tr>
                            <td>${p.id}</td>
                            <td>
                                <strong>${p.title || 'Untitled'}</strong>
                                ${p.brand ? `<div style="color:#64748b; font-size:12px;">Brand: ${p.brand}</div>` : ''}
                            </td>
                            <td>
                                <div class="category-path">${cleanMain}</div>
                                ${isLow && (cleanAlt1 || cleanAlt2) ? `
                                    <div class="alts">
                                        <div style="font-size:11px; font-weight:bold; color:#dc2626; margin-bottom:2px;">Alternative Suggestions:</div>
                                        ${cleanAlt1 ? `<div><strong>Alt 1:</strong> ${cleanAlt1}</div>` : ''}
                                        ${cleanAlt2 ? `<div style="margin-top:2px;"><strong>Alt 2:</strong> ${cleanAlt2}</div>` : ''}
                                    </div>
                                ` : ''}
                            </td>
                            <td>
                                <span class="badge ${isLow ? 'low' : 'high'}">${p.confidence_score}%</span>
                                ${isLow ? '<span class="review-warning">Review Needed</span>' : ''}
                            </td>
                            <td>${formatAttributes(p.attributes)}</td>
                            <td>
                                ${p.approved ? '<span style="color:#16a34a; font-weight:bold; margin-right:4px;">✅ Approved</span>' : `
                                    <button class="btn-approve" onclick="approveRecord(${p.id})">Approve</button>
                                `}
                                <button class="btn-edit" onclick="editCategory(${p.id}, '${cleanMain}')">Edit</button>
                            </td>
                        </tr>
                    `;
                }).join('');
                loadStats();
            }

            function setFilter(filter, elem) {
                currentFilter = filter;
                currentPage = 1;
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                elem.classList.add('active');
                loadTable();
            }

            function changePage(delta) {
                currentPage += delta;
                if (currentPage < 1) currentPage = 1;
                loadTable();
            }

            async function approveRecord(id) {
                await fetch(`/api/approve/${id}`, { method: 'POST' });
                loadTable();
            }

            async function editCategory(id, current) {
                const updated = prompt('Enter updated Shopify category path:', current);
                if (updated && updated !== current) {
                    await fetch(`/api/update-category/${id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ category: updated })
                    });
                    loadTable();
                }
            }

            loadTable();
        </script>
    </body>
    </html>
    """