"""FastAPI read-only API over the same SQL-backed retail data."""
from fastapi import FastAPI, HTTPException, Query
from retailops_mcp.db.database import get_connection, initialize_database, rows_to_dicts

app = FastAPI(
    title="RetailOps API",
    description="Read-only retail procurement, inventory and vendor API.",
    version="1.0.0",
)

@app.on_event("startup")
def startup():
    initialize_database()

@app.get("/health")
def health():
    return {"status": "ok", "service": "retailops-api"}

@app.get("/purchase-orders")
def purchase_orders(vendor: str = Query(default=""), site: str = Query(default="")):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.*, v.vendor_name
            FROM purchase_orders p JOIN vendors v ON v.vendor_id = p.vendor_id
            WHERE (? = '' OR LOWER(v.vendor_name) LIKE '%' || LOWER(?) || '%')
              AND (? = '' OR UPPER(p.site) = UPPER(?))
            ORDER BY p.po_id
        """, (vendor, vendor, site, site)).fetchall()
    return {"count": len(rows), "items": rows_to_dicts(rows)}

@app.get("/purchase-orders/{po_id}")
def purchase_order(po_id: str):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT p.*, v.vendor_name
            FROM purchase_orders p JOIN vendors v ON v.vendor_id = p.vendor_id
            WHERE UPPER(p.po_id) = UPPER(?)
        """, (po_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return dict(row)

@app.get("/inventory/low-stock")
def low_stock():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT sku, site, available_qty, minimum_qty,
                   minimum_qty - available_qty AS shortage_qty
            FROM inventory WHERE available_qty < minimum_qty
            ORDER BY shortage_qty DESC
        """).fetchall()
    return {"count": len(rows), "items": rows_to_dicts(rows)}
