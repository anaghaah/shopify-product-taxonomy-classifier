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
    cursor.execute("SELECT COUNT(*) FROM products WHERE approved = 1")
    approved = cursor.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "review": review,
        "approved": approved
    }

@app.get("/api/products")
def get_products(page: int = 1, page_size: int = 50, status: str = "ALL", q: str = ""):
    offset = (page - 1) * page_size
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if status == "REVIEW":
        query += " AND manual_review = 1"
    elif status == "APPROVED":
        query += " AND approved = 1"
    elif status == "COMPLETED":
        query += " AND status = 'COMPLETED'"

    if q.strip():
        query += " AND (title LIKE ? OR brand LIKE ? OR predicted_category LIKE ?)"
        wildcard = f"%{q.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    query += " LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    cursor.execute(query, tuple(params))
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
        <title>Shopify Taxonomy Intelligence Suite</title>
        <!-- Google Fonts & Icons -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #4f46e5;
                --primary-hover: #4338ca;
                --bg: #f8fafc;
                --surface: #ffffff;
                --border: #e2e8f0;
                --text-main: #0f172a;
                --text-muted: #64748b;
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
            }

            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                background: var(--bg);
                color: var(--text-main);
                padding: 32px 40px;
                min-height: 100vh;
            }

            .container { max-width: 1440px; margin: 0 auto; }

            /* Navigation & Brand Header */
            .navbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 28px;
            }
            .brand {
                display: flex;
                align-items: center;
                gap: 14px;
            }
            .logo-icon {
                width: 44px;
                height: 44px;
                background: linear-gradient(135deg, #4f46e5, #06b6d4);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 700;
                font-size: 20px;
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
            }
            .brand h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }
            .brand p { font-size: 13px; color: var(--text-muted); }

            /* Top KPI Metric Cards */
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 28px;
            }
            .metric-card {
                background: var(--surface);
                padding: 20px 24px;
                border-radius: 16px;
                border: 1px solid var(--border);
                box-shadow: 0 2px 4px rgba(0,0,0,0.02);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.04);
            }
            .metric-label { font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
            .metric-value { font-size: 28px; font-weight: 700; margin-top: 6px; }

            /* Action Controls & Search Toolbar */
            .toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
                margin-bottom: 18px;
                flex-wrap: wrap;
            }
            .search-box {
                position: relative;
                flex: 1;
                max-width: 420px;
            }
            .search-box input {
                width: 100%;
                padding: 10px 16px 10px 38px;
                border-radius: 10px;
                border: 1px solid var(--border);
                background: white;
                font-size: 14px;
                font-family: inherit;
                outline: none;
                transition: border-color 0.2s ease;
            }
            .search-box input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }
            .search-icon {
                position: absolute;
                left: 14px;
                top: 50%;
                transform: translateY(-50%);
                color: var(--text-muted);
                font-size: 14px;
            }
            .filter-group { display: flex; gap: 8px; }
            .filter-pill {
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                border: 1px solid var(--border);
                background: white;
                color: var(--text-muted);
                transition: all 0.15s ease;
            }
            .filter-pill:hover { background: #f1f5f9; color: var(--text-main); }
            .filter-pill.active { background: #0f172a; color: white; border-color: #0f172a; }

            /* Main Table Component */
            .table-card {
                background: var(--surface);
                border-radius: 16px;
                border: 1px solid var(--border);
                box-shadow: 0 4px 16px rgba(0,0,0,0.03);
                overflow: hidden;
            }
            table { width: 100%; border-collapse: collapse; text-align: left; }
            thead { background: #f8fafc; border-bottom: 1px solid var(--border); }
            th {
                padding: 14px 20px;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--text-muted);
            }
            td {
                padding: 16px 20px;
                border-bottom: 1px solid #f1f5f9;
                font-size: 14px;
                vertical-align: top;
            }
            tr:hover td { background-color: #fbfcfe; }

            /* Custom Badges and Tags */
            .badge {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
            }
            .badge-high { background: #dcfce7; color: #15803d; }
            .badge-low { background: #fee2e2; color: #b91c1c; }

            .category-tag {
                color: #2563eb;
                font-weight: 600;
                font-size: 13px;
                line-height: 1.4;
            }
            .alts-container {
                margin-top: 8px;
                background: #f8fafc;
                border-radius: 8px;
                padding: 8px 12px;
                border: 1px dashed var(--border);
                font-size: 12px;
            }
            .alts-title { font-size: 11px; font-weight: 700; color: #dc2626; margin-bottom: 4px; text-transform: uppercase; }
            
            .attr-pill {
                display: inline-block;
                background: #f1f5f9;
                color: #334155;
                padding: 3px 8px;
                border-radius: 6px;
                font-size: 11px;
                margin: 2px;
                border: 1px solid var(--border);
            }
            .attr-pill strong { color: #0f172a; font-weight: 600; }

            /* Action Buttons */
            .btn-group { display: flex; gap: 6px; align-items: center; }
            .btn {
                padding: 7px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                border: none;
                transition: all 0.15s ease;
            }
            .btn-approve { background: #10b981; color: white; }
            .btn-approve:hover { background: #059669; }
            .btn-edit { background: white; color: #334155; border: 1px solid var(--border); }
            .btn-edit:hover { background: #f1f5f9; color: var(--text-main); }
            .approved-chip {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                font-weight: 600;
                color: #10b981;
                font-size: 12px;
            }

            /* Pagination */
            .pagination-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 24px;
                background: white;
                border-top: 1px solid var(--border);
            }
            .page-btn {
                padding: 8px 16px;
                border-radius: 8px;
                border: 1px solid var(--border);
                background: white;
                font-weight: 600;
                font-size: 13px;
                cursor: pointer;
                color: var(--text-main);
                transition: background 0.15s;
            }
            .page-btn:hover:not(:disabled) { background: #f8fafc; }
            .page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

            /* Modern Custom Modal */
            .modal-overlay {
                position: fixed;
                inset: 0;
                background: rgba(15, 23, 42, 0.4);
                backdrop-filter: blur(4px);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            .modal-box {
                background: white;
                border-radius: 16px;
                padding: 24px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }
            .modal-title { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
            .modal-input {
                width: 100%;
                padding: 10px 14px;
                border-radius: 8px;
                border: 1px solid var(--border);
                font-size: 14px;
                margin-top: 12px;
                font-family: inherit;
            }
            .modal-actions {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Navbar -->
            <div class="navbar">
                <div class="brand">
                    <div class="logo-icon">🛍️</div>
                    <div>
                        <h1>Shopify Taxonomy Intelligence</h1>
                        <p>Enterprise Product Categorization & Attribute Extraction Platform</p>
                    </div>
                </div>
            </div>

            <!-- Metric Cards -->
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Catalog</div>
                    <div class="metric-value" id="stat-total">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Categorized</div>
                    <div class="metric-value" id="stat-completed" style="color: var(--primary);">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Needs Review (&lt;35%)</div>
                    <div class="metric-value" id="stat-review" style="color: var(--danger);">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Approved</div>
                    <div class="metric-value" id="stat-approved" style="color: var(--success);">-</div>
                </div>
            </div>

            <!-- Search and Filters -->
            <div class="toolbar">
                <div class="search-box">
                    <span class="search-icon">🔍</span>
                    <input type="text" id="search-input" placeholder="Search by title, brand, or category..." oninput="onSearch()">
                </div>
                <div class="filter-group">
                    <button class="filter-pill active" onclick="setFilter('ALL', this)">All Items</button>
                    <button class="filter-pill" onclick="setFilter('REVIEW', this)">Needs Review</button>
                    <button class="filter-pill" onclick="setFilter('APPROVED', this)">Approved Only</button>
                </div>
            </div>

            <!-- Main Data Table -->
            <div class="table-card">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 60px;">ID</th>
                            <th style="width: 340px;">Product & Brand</th>
                            <th>Shopify Taxonomy Path</th>
                            <th style="width: 120px;">Confidence</th>
                            <th style="width: 180px;">Detected Attributes</th>
                            <th style="width: 170px;">Action</th>
                        </tr>
                    </thead>
                    <tbody id="rows">
                        <tr><td colspan="6" style="text-align:center; padding: 40px; color: var(--text-muted);">Loading catalog...</td></tr>
                    </tbody>
                </table>
                <div class="pagination-bar">
                    <button class="page-btn" id="prev-btn" onclick="changePage(-1)">Previous</button>
                    <span id="page-info" style="font-size: 13px; font-weight: 600; color: var(--text-muted);">Page 1</span>
                    <button class="page-btn" id="next-btn" onclick="changePage(1)">Next</button>
                </div>
            </div>
        </div>

        <!-- Custom Edit Modal -->
        <div class="modal-overlay" id="edit-modal">
            <div class="modal-box">
                <div class="modal-title">Manual Category Override</div>
                <p style="font-size: 13px; color: var(--text-muted);">Update the taxonomy path for this product:</p>
                <input type="text" id="modal-cat-input" class="modal-input">
                <div class="modal-actions">
                    <button class="btn btn-edit" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-approve" style="background: var(--primary);" onclick="submitModalEdit()">Save Changes</button>
                </div>
            </div>
        </div>

        <script>
            let currentPage = 1;
            let currentFilter = 'ALL';
            let searchQuery = '';
            let activeEditId = null;
            let searchTimeout = null;
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
                    return keys.map(k => `<span class="attr-pill">${k}: <strong>${parsed[k]}</strong></span>`).join('');
                } catch(e) {
                    return '<span style="color:#94a3b8;">—</span>';
                }
            }

            async function loadStats() {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stat-total').innerText = data.total.toLocaleString();
                document.getElementById('stat-completed').innerText = data.completed.toLocaleString();
                document.getElementById('stat-review').innerText = data.review.toLocaleString();
                document.getElementById('stat-approved').innerText = data.approved.toLocaleString();
            }

            async function loadTable() {
                const url = `/api/products?page=${currentPage}&page_size=${pageSize}&status=${currentFilter}&q=${encodeURIComponent(searchQuery)}`;
                const res = await fetch(url);
                const data = await res.json();
                const tbody = document.getElementById('rows');

                document.getElementById('page-info').innerText = `Page ${currentPage}`;
                document.getElementById('prev-btn').disabled = (currentPage === 1);
                document.getElementById('next-btn').disabled = (data.length < pageSize);

                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 40px; color: var(--text-muted);">No products found matching the criteria.</td></tr>';
                    return;
                }

                tbody.innerHTML = data.map(p => {
                    const isLow = p.confidence_score < 35.0;
                    const cleanMain = cleanCategory(p.predicted_category);
                    const cleanAlt1 = cleanCategory(p.alt_category_1);
                    const cleanAlt2 = cleanCategory(p.alt_category_2);

                    return `
                        <tr>
                            <td style="color: var(--text-muted); font-weight: 500;">#${p.id}</td>
                            <td>
                                <div style="font-weight: 600; color: var(--text-main); margin-bottom: 2px;">${p.title || 'Untitled Product'}</div>
                                ${p.brand ? `<div style="font-size:12px; color:var(--text-muted);">Vendor: <span style="font-weight:500; color:#334155;">${p.brand}</span></div>` : ''}
                            </td>
                            <td>
                                <div class="category-tag">${cleanMain}</div>
                                ${isLow && (cleanAlt1 || cleanAlt2) ? `
                                    <div class="alts-container">
                                        <div class="alts-title">Alternative Predictions</div>
                                        ${cleanAlt1 ? `<div>• ${cleanAlt1}</div>` : ''}
                                        ${cleanAlt2 ? `<div style="margin-top:2px;">• ${cleanAlt2}</div>` : ''}
                                    </div>
                                ` : ''}
                            </td>
                            <td>
                                <span class="badge ${isLow ? 'badge-low' : 'badge-high'}">
                                    ${p.confidence_score}%
                                </span>
                            </td>
                            <td>${formatAttributes(p.attributes)}</td>
                            <td>
                                <div class="btn-group">
                                    ${p.approved ? '<span class="approved-chip">✓ Approved</span>' : `
                                        <button class="btn btn-approve" onclick="approveRecord(${p.id})">Approve</button>
                                    `}
                                    <button class="btn btn-edit" onclick="openModal(${p.id}, '${cleanMain.replace(/'/g, "\\\\'")}')">Edit</button>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join('');
                loadStats();
            }

            function setFilter(filter, elem) {
                currentFilter = filter;
                currentPage = 1;
                document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
                elem.classList.add('active');
                loadTable();
            }

            function changePage(delta) {
                currentPage += delta;
                if (currentPage < 1) currentPage = 1;
                loadTable();
            }

            function onSearch() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    searchQuery = document.getElementById('search-input').value;
                    currentPage = 1;
                    loadTable();
                }, 300);
            }

            async function approveRecord(id) {
                await fetch(`/api/approve/${id}`, { method: 'POST' });
                loadTable();
            }

            function openModal(id, currentCategory) {
                activeEditId = id;
                document.getElementById('modal-cat-input').value = currentCategory;
                document.getElementById('edit-modal').style.display = 'flex';
            }

            function closeModal() {
                document.getElementById('edit-modal').style.display = 'none';
                activeEditId = null;
            }

            async function submitModalEdit() {
                const val = document.getElementById('modal-cat-input').value.trim();
                if (val && activeEditId) {
                    await fetch(`/api/update-category/${activeEditId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ category: val })
                    });
                    closeModal();
                    loadTable();
                }
            }

            loadTable();
        </script>
    </body>
    </html>
    """