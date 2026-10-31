"""Read-only Procurement MCP server backed by SQL."""
from mcp.server.fastmcp import FastMCP
from retailops_mcp.db.database import get_connection, initialize_database, rows_to_dicts

mcp = FastMCP("RetailOps Procurement MCP")

@mcp.tool()
def search_purchase_orders(vendor_name: str = "", site: str = "") -> list[dict]:
    """Search purchase orders by optional vendor name and site."""
    initialize_database()
    sql = """
        SELECT p.*, v.vendor_name
        FROM purchase_orders p
        JOIN vendors v ON v.vendor_id = p.vendor_id
        WHERE (? = '' OR LOWER(v.vendor_name) LIKE '%' || LOWER(?) || '%')
          AND (? = '' OR UPPER(p.site) = UPPER(?))
        ORDER BY p.po_id
    """
    with get_connection() as conn:
        return rows_to_dicts(conn.execute(sql, (vendor_name, vendor_name, site, site)).fetchall())

@mcp.tool()
def get_purchase_order(po_id: str) -> dict:
    """Retrieve a purchase order by its exact PO ID."""
    initialize_database()
    with get_connection() as conn:
        row = conn.execute("""
            SELECT p.*, v.vendor_name
            FROM purchase_orders p JOIN vendors v ON v.vendor_id = p.vendor_id
            WHERE UPPER(p.po_id) = UPPER(?)
        """, (po_id.strip(),)).fetchone()
    return dict(row) if row else {"found": False, "message": f"PO {po_id} was not found"}

@mcp.tool()
def calculate_po_quantities(po_id: str) -> dict:
    """Calculate pending ASN, pending GRN against ASN, and unreceived PO quantity."""
    po = get_purchase_order(po_id)
    if not po.get("po_id"):
        return po
    return {
        "po_id": po_id,
        "po_qty": po["po_qty"],
        "asn_qty": po["asn_qty"],
        "grn_qty": po["grn_qty"],
        "pending_asn_qty": max(po["po_qty"] - po["asn_qty"], 0),
        "pending_grn_vs_asn_qty": max(po["asn_qty"] - po["grn_qty"], 0),
        "unreceived_vs_po_qty": max(po["po_qty"] - po["grn_qty"], 0),
    }

@mcp.resource("retailops://procurement/po-policy")
def po_policy() -> str:
    """Read the demo PO/ASN/GRN interpretation policy."""
    return (
        "Compare PO, ASN and GRN quantities separately. Pending ASN = PO - ASN. "
        "Pending GRN against ASN = ASN - GRN. Unreceived against PO = PO - GRN. "
        "Flag negative or inconsistent source values for human review; do not update source records."
    )

@mcp.prompt()
def po_exception_review(po_id: str) -> str:
    """Generate a reusable prompt to review a purchase-order exception."""
    return (
        f"Review {po_id}. Retrieve the PO and quantity details, explain each quantity gap, "
        "separate facts from assumptions, and recommend a human-reviewed next step. "
        "Do not change source records."
    )

if __name__ == "__main__":
    initialize_database()
    mcp.run(transport="stdio")
