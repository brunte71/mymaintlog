#!/usr/bin/env python3
"""Migrate existing CSV data files to the new SQLite database.

Run this script once after upgrading from the CSV-based backend to SQLite.
It reads each CSV file that is present and inserts the rows into the
corresponding SQLite table, skipping rows whose primary key already exists.

Usage:
    python scripts/migrate_csv_to_sqlite.py
"""
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_handler import DataHandler, DATA_DIR


# Map CSV filename → (table name, primary key column)
CSV_TABLE_MAP = {
    "objects.csv":      ("objects",      "object_id"),
    "services.csv":     ("services",     "service_id"),
    "reminders.csv":    ("reminders",    "reminder_id"),
    "reports.csv":      ("reports",      "report_id"),
    "fault_reports.csv": ("fault_reports", "fault_id"),
    "meter_units.csv":  ("meter_units",  "unit"),
}


def migrate_csv(conn: sqlite3.Connection, csv_path: Path, table: str, pk: str):
    """Import rows from *csv_path* into *table*, skipping existing primary keys."""
    if not csv_path.exists():
        print(f"  Skipping {csv_path.name} – file not found.")
        return 0

    # keep_default_na=False preserves empty strings as "" rather than NaN so
    # that empty text fields survive the migration correctly.
    df = pd.read_csv(csv_path, keep_default_na=False)
    if df.empty:
        print(f"  Skipping {csv_path.name} – empty file.")
        return 0

    # Fetch existing primary keys to avoid duplicates
    existing = {row[0] for row in conn.execute(f"SELECT {pk} FROM {table}").fetchall()}

    inserted = 0
    for _, row in df.iterrows():
        pk_val = row.get(pk)
        if pk_val in existing:
            continue
        # Build INSERT with only the columns present in the CSV
        cols = [c for c in df.columns if c in row.index]
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        values = [None if pd.isna(row[c]) else row[c] for c in cols]
        try:
            conn.execute(
                f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
                values,
            )
            inserted += 1
        except Exception as exc:
            print(f"  Warning: could not insert row {pk_val}: {exc}")

    return inserted


def main():
    print("ServiceMgr – CSV → SQLite migration")
    print("=" * 40)

    # Initialise the database (creates tables if needed)
    handler = DataHandler()

    with handler._get_conn() as conn:
        for csv_name, (table, pk) in CSV_TABLE_MAP.items():
            csv_path = DATA_DIR / csv_name
            count = migrate_csv(conn, csv_path, table, pk)
            if count:
                print(f"  {csv_name}: {count} row(s) imported into '{table}'.")

    print("=" * 40)
    print("Migration complete.  The SQLite database is at:")
    print(f"  {DATA_DIR / 'servicemgr.db'}")
    print()
    print("You may archive or delete the CSV files once you have verified")
    print("that all data appears correctly in the application.")


if __name__ == "__main__":
    main()
