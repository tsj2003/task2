"""Ingest JSONL files from the SAP O2C dataset into SQLite."""
import json
import sqlite3
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import DATABASE_PATH
from app.database import get_connection, create_schema

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Map folder names to table names and their column mappings
ENTITY_MAP = {
    "business_partners": "business_partners",
    "customer_company_assignments": "customer_company_assignments",
    "customer_sales_area_assignments": "customer_sales_area_assignments",
    "sales_order_headers": "sales_order_headers",
    "sales_order_items": "sales_order_items",
    "outbound_delivery_headers": "outbound_delivery_headers",
    "billing_document_cancellations": "billing_documents",
    "journal_entry_items_accounts_receivable": "journal_entries",
    "payments_accounts_receivable": "payments",
    "plants": "plants",
    "product_descriptions": "product_descriptions",
    "product_plants": "product_plants",
    "product_storage_locations": "product_storage_locations",
}

# Fields that should be cast to REAL
NUMERIC_FIELDS = {
    "totalNetAmount", "netAmount", "requestedQuantity",
    "amountInTransactionCurrency", "amountInCompanyCodeCurrency",
}

# Fields that are nested time objects {hours, minutes, seconds}
TIME_OBJECT_FIELDS = {"creationTime", "actualGoodsMovementTime"}


def flatten_time(val):
    """Convert {hours, minutes, seconds} dict to 'HH:MM:SS' string."""
    if isinstance(val, dict) and "hours" in val:
        return f"{val['hours']:02d}:{val['minutes']:02d}:{val['seconds']:02d}"
    return val


def clean_value(key: str, val):
    """Clean a single field value for SQLite insertion."""
    if val is None or val == "":
        return None
    if key in TIME_OBJECT_FIELDS:
        return flatten_time(val)
    if key in NUMERIC_FIELDS:
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    if isinstance(val, bool):
        return 1 if val else 0
    return str(val) if not isinstance(val, str) else val


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    """Get column names for a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def ingest_entity(conn: sqlite3.Connection, folder_path: Path, table_name: str):
    """Ingest all JSONL files from a folder into the target table."""
    columns = get_table_columns(conn, table_name)
    if not columns:
        logger.error("Table %s has no columns — schema not created?", table_name)
        return 0

    jsonl_files = sorted(folder_path.glob("*.jsonl"))
    if not jsonl_files:
        logger.warning("No JSONL files found in %s", folder_path)
        return 0

    total_inserted = 0
    total_skipped = 0

    for jf in jsonl_files:
        with open(jf, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning("Skipping malformed JSON in %s line %d: %s", jf.name, line_num, e)
                    total_skipped += 1
                    continue

                # Only keep columns that exist in the table
                cleaned = {}
                for col in columns:
                    if col in record:
                        cleaned[col] = clean_value(col, record[col])
                    else:
                        cleaned[col] = None

                placeholders = ", ".join(["?"] * len(columns))
                col_names = ", ".join(columns)
                values = [cleaned[c] for c in columns]

                try:
                    conn.execute(
                        f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})",
                        values,
                    )
                    total_inserted += 1
                except sqlite3.Error as e:
                    logger.warning("Skipping record in %s: %s", jf.name, e)
                    total_skipped += 1

    conn.commit()
    logger.info(
        "  %s: inserted=%d, skipped=%d (from %d files)",
        table_name, total_inserted, total_skipped, len(jsonl_files),
    )
    return total_inserted


def run_ingestion(raw_data_dir: str | Path):
    """Run full ingestion pipeline."""
    raw_data_dir = Path(raw_data_dir)
    if not raw_data_dir.exists():
        logger.error("Raw data directory not found: %s", raw_data_dir)
        sys.exit(1)

    logger.info("Creating database schema...")
    create_schema()
    conn = get_connection()

    logger.info("Starting data ingestion from %s", raw_data_dir)
    total = 0
    for folder_name, table_name in ENTITY_MAP.items():
        folder_path = raw_data_dir / folder_name
        if not folder_path.exists():
            logger.warning("Folder not found, skipping: %s", folder_name)
            continue
        count = ingest_entity(conn, folder_path, table_name)
        total += count

    logger.info("Ingestion complete. Total records: %d", total)

    # Print summary
    logger.info("\n=== INGESTION SUMMARY ===")
    for folder_name, table_name in ENTITY_MAP.items():
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        logger.info("  %-40s → %-35s : %d rows", folder_name, table_name, count)


if __name__ == "__main__":
    raw_dir = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent / "data" / "raw")
    run_ingestion(raw_dir)
