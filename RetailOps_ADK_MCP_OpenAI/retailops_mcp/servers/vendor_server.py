"""Read-only Vendor MCP server backed by SQL."""
from mcp.server.fastmcp import FastMCP
from retailops_mcp.db.database import get_connection, initialize_database

mcp = FastMCP("RetailOps Vendor MCP")

@mcp.tool()
def get_vendor(vendor_id: str) -> dict:
    """Retrieve vendor master details by vendor ID."""
    initialize_database()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT vendor_id, vendor_name, email FROM vendors WHERE UPPER(vendor_id)=UPPER(?)",
            (vendor_id.strip(),),
        ).fetchone()
    return dict(row) if row else {"found": False, "message": f"Vendor {vendor_id} was not found"}

@mcp.tool()
def get_vendor_po_performance(vendor_id: str) -> dict:
    """Summarize PO, ASN, and GRN quantities for one vendor."""
    initialize_database()
    with get_connection() as conn:
        row = conn.execute("""
            SELECT v.vendor_id, v.vendor_name,
                   COUNT(p.po_id) AS po_count,
                   COALESCE(SUM(p.po_qty), 0) AS total_po_qty,
                   COALESCE(SUM(p.asn_qty), 0) AS total_asn_qty,
                   COALESCE(SUM(p.grn_qty), 0) AS total_grn_qty
            FROM vendors v
            LEFT JOIN purchase_orders p ON p.vendor_id = v.vendor_id
            WHERE UPPER(v.vendor_id) = UPPER(?)
            GROUP BY v.vendor_id, v.vendor_name
        """, (vendor_id.strip(),)).fetchone()
    if not row:
        return {"found": False, "message": f"Vendor {vendor_id} was not found"}
    result = dict(row)
    po_qty = result["total_po_qty"]
    result["asn_fill_rate_pct"] = round(result["total_asn_qty"] / po_qty * 100, 2) if po_qty else 0
    result["grn_completion_pct"] = round(result["total_grn_qty"] / po_qty * 100, 2) if po_qty else 0
    return result

@mcp.prompt()
def vendor_review(vendor_id: str) -> str:
    """Generate a reusable vendor performance review prompt."""
    return (
        f"Review vendor {vendor_id} using retrieved PO, ASN and GRN facts. "
        "Summarize measurable performance, identify data gaps and recommend follow-up. "
        "Do not invent delivery delays or send communications."
    )


@mcp.tool()
def get_all_vendor_performance() -> list[dict]:
    """
    Retrieve performance metrics for all vendors.

    A vendor is problematic if either:
    1. ASN fill rate is below 90%.
    2. GRN completion rate is below 90%.
    """
    initialize_database()

    # Step 1: Retrieve all vendor performance data from SQL
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                v.vendor_id,
                v.vendor_name,
                COUNT(p.po_id) AS po_count,
                COALESCE(SUM(p.po_qty), 0) AS total_po_qty,
                COALESCE(SUM(p.asn_qty), 0) AS total_asn_qty,
                COALESCE(SUM(p.grn_qty), 0) AS total_grn_qty
            FROM vendors v
            LEFT JOIN purchase_orders p
                ON p.vendor_id = v.vendor_id
            GROUP BY v.vendor_id, v.vendor_name
            ORDER BY v.vendor_id
        """).fetchall()

    # Step 2: Prepare the result list
    results = []

    # Step 3: Process each vendor
    for row in rows:
        result = dict(row)

        po_qty = result["total_po_qty"]
        asn_qty = result["total_asn_qty"]
        grn_qty = result["total_grn_qty"]

        # Step 4: Calculate performance percentages
        if po_qty > 0:
            asn_rate = round((asn_qty / po_qty) * 100, 2)
            grn_rate = round((grn_qty / po_qty) * 100, 2)

            # Step 5: Apply the 90% business rule
            is_problematic = (
                asn_rate < 90 or grn_rate < 90
            )

            # Step 6: Identify the reasons
            reasons = []

            if asn_rate < 90:
                reasons.append("ASN fill rate below 90%")

            if grn_rate < 90:
                reasons.append("GRN completion rate below 90%")

            # Step 7: Add calculated values
            result["asn_fill_rate_pct"] = asn_rate
            result["grn_completion_pct"] = grn_rate
            result["is_problematic"] = is_problematic
            result["problem_reasons"] = reasons

            result["status"] = (
                "Problematic" if is_problematic else "Healthy"
            )

        else:
            # Step 8: Handle vendors without PO data
            result["asn_fill_rate_pct"] = None
            result["grn_completion_pct"] = None
            result["is_problematic"] = False
            result["problem_reasons"] = []
            result["status"] = "Insufficient data"

        results.append(result)

    # Step 9: Return all vendor records
    return results


if __name__ == "__main__":
    initialize_database()
    mcp.run(transport="stdio")
