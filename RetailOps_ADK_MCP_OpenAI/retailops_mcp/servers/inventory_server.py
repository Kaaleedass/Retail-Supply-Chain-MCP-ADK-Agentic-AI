"""Read-only Inventory MCP server backed by SQL."""
from mcp.server.fastmcp import FastMCP
from retailops_mcp.db.database import get_connection, initialize_database, rows_to_dicts

mcp = FastMCP("RetailOps Inventory MCP")

@mcp.tool()
def get_inventory(site: str = "") -> list[dict]:
    """Retrieve inventory, optionally filtered by site."""
    initialize_database()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT sku, site, available_qty, minimum_qty
            FROM inventory
            WHERE (? = '' OR UPPER(site) = UPPER(?))
            ORDER BY site, sku
        """, (site, site)).fetchall()
    return rows_to_dicts(rows)

@mcp.tool()
def find_low_stock() -> list[dict]:
    """Find inventory below its configured minimum quantity."""
    initialize_database()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT sku, site, available_qty, minimum_qty,
                   (minimum_qty - available_qty) AS shortage_qty
            FROM inventory
            WHERE available_qty < minimum_qty
            ORDER BY shortage_qty DESC
        """).fetchall()
    return rows_to_dicts(rows)

@mcp.tool()
def get_grn_pending_summary() -> list[dict]:
    """Summarize PO quantity not yet received as GRN."""
    initialize_database()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.po_id, v.vendor_name, p.site, p.po_qty, p.grn_qty,
                   (p.po_qty - p.grn_qty) AS pending_grn_qty
            FROM purchase_orders p
            JOIN vendors v ON v.vendor_id = p.vendor_id
            WHERE p.po_qty > p.grn_qty
            ORDER BY pending_grn_qty DESC
        """).fetchall()
    return rows_to_dicts(rows)

@mcp.resource("retailops://inventory/stock-policy")
def stock_policy() -> str:
    """Read the sample inventory threshold policy."""
    return (
        "Flag an SKU when available_qty is below minimum_qty. "
        "A stock transfer recommendation requires confirmation of source-site availability."
    )

if __name__ == "__main__":
    initialize_database()
    mcp.run(transport="stdio")
