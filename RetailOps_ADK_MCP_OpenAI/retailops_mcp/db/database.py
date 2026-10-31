"""SQLite database setup and repository helpers.

SQLite is used as the initial SQL database so the project runs locally
without installing a separate database server. The SQL statements are
portable in concept; adapt data types/placeholders when moving to SQL Server
or PostgreSQL.
"""
import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("RETAILOPS_DB_PATH", PROJECT_ROOT / "data" / "retailops.db"))

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database() -> None:
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS vendors (
            vendor_id TEXT PRIMARY KEY,
            vendor_name TEXT NOT NULL,
            email TEXT
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_id TEXT PRIMARY KEY,
            vendor_id TEXT NOT NULL,
            site TEXT NOT NULL,
            po_qty INTEGER NOT NULL CHECK (po_qty >= 0),
            asn_qty INTEGER NOT NULL CHECK (asn_qty >= 0),
            grn_qty INTEGER NOT NULL CHECK (grn_qty >= 0),
            order_date TEXT NOT NULL,
            expected_delivery TEXT NOT NULL,
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        );

        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT NOT NULL,
            site TEXT NOT NULL,
            available_qty INTEGER NOT NULL CHECK (available_qty >= 0),
            minimum_qty INTEGER NOT NULL CHECK (minimum_qty >= 0),
            PRIMARY KEY (sku, site)
        );
        """)
        vendor_count = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
        if vendor_count == 0:
            conn.executemany(
                "INSERT INTO vendors(vendor_id, vendor_name, email) VALUES (?, ?, ?)",
                [
                    ("V001", "ABC Textiles", "vendor001@example.com"),
                    ("V002", "XYZ Garments", "vendor002@example.com"),
                    ("V003", "Metro Apparel", "vendor003@example.com"),
                ],
            )
            conn.executemany(
                """INSERT INTO purchase_orders
                (po_id, vendor_id, site, po_qty, asn_qty, grn_qty, order_date, expected_delivery)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    ("PO1001", "V001", "BLR01", 1000, 800, 650, "2026-10-10", "2026-11-05"),
                    ("PO1002", "V002", "CHN02", 500, 500, 500, "2026-10-12", "2026-11-07"),
                    ("PO1003", "V001", "BLR02", 750, 300, 250, "2026-10-14", "2026-11-09"),
                    ("PO1004", "V003", "HYD01", 1200, 900, 0, "2026-10-15", "2026-11-10"),
                ],
            )
            conn.executemany(
                """INSERT INTO inventory(sku, site, available_qty, minimum_qty)
                VALUES (?, ?, ?, ?)""",
                [
                    ("SKU100", "BLR01", 35, 50),
                    ("SKU200", "CHN02", 180, 100),
                    ("SKU300", "HYD01", 12, 40),
                ],
            )

def rows_to_dicts(rows):
    return [dict(row) for row in rows]
