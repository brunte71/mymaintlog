#!/usr/bin/env python3
"""Normalise `object_type` values in the mymaintlog database.

All object_type values written through DataHandler are already normalised
automatically.  Run this script once after migrating from legacy CSV data
to clean up any non-canonical values that may have been imported.

Usage:
    python scripts/migrate_object_types.py
"""
import sys
from pathlib import Path

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_handler import DataHandler


def main():
    handler = DataHandler()
    with handler._get_conn() as conn:
        rows = conn.execute("SELECT object_id, object_type FROM objects").fetchall()
        changes = 0
        for object_id, raw_type in rows:
            canonical = handler.normalize_object_type(raw_type)
            if raw_type != canonical:
                conn.execute(
                    "UPDATE objects SET object_type = ? WHERE object_id = ?",
                    (canonical, object_id),
                )
                changes += 1
    print(f"Migration complete. {changes} record(s) updated.")


if __name__ == "__main__":
    main()
