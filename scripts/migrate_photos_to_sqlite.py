#!/usr/bin/env python3
"""Migrate fault photos from the filesystem to SQLite BLOB storage.

Run this script once if you have existing photos stored in data/fault_photos/.
It reads each photo file referenced in fault_reports.photo_paths, stores it
as a BLOB in the new fault_photos table, then clears the photo_paths column
for that fault report.

The script is idempotent: fault reports that already have rows in fault_photos
are skipped so it is safe to run more than once.

Usage:
    python scripts/migrate_photos_to_sqlite.py
"""

import sys
import mimetypes
from pathlib import Path

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_handler import DataHandler, DATA_DIR


def guess_mime_type(filename):
    """Guess MIME type from filename, defaulting to image/jpeg."""
    mt, _ = mimetypes.guess_type(filename)
    return mt or "image/jpeg"


def main():
    print("mymaintlog – fault photos → SQLite BLOB migration")
    print("=" * 50)

    handler = DataHandler()
    df = handler.get_fault_reports()

    if df.empty:
        print("No fault reports found – nothing to migrate.")
        return

    total_migrated = 0
    project_root = Path(__file__).parent.parent

    for _, row in df.iterrows():
        fault_id = row["fault_id"]
        photo_paths_val = str(row.get("photo_paths", "")) if row.get("photo_paths") else ""
        photo_paths = [p for p in photo_paths_val.split(";") if p and p.lower() != "nan"]

        if not photo_paths:
            continue

        # Skip if photos already migrated for this fault report
        existing = handler.get_fault_photos(fault_id)
        if existing:
            print(f"  {fault_id}: {len(existing)} photo(s) already in DB – skipping.")
            continue

        migrated = 0
        for path_str in photo_paths:
            photo_path = Path(path_str)
            if not photo_path.exists():
                # Try relative to project root
                photo_path = project_root / path_str
            if not photo_path.exists():
                print(f"  {fault_id}: photo not found at '{path_str}' – skipping file.")
                continue

            data = photo_path.read_bytes()
            mime_type = guess_mime_type(photo_path.name)
            handler.save_fault_photo(fault_id, photo_path.name, mime_type, data)
            migrated += 1
            total_migrated += 1

        if migrated > 0:
            # Clear photo_paths now that photos are stored in SQLite
            handler.update_fault_report(fault_id, photo_paths="")
            print(f"  {fault_id}: {migrated} photo(s) migrated.")

    print("=" * 50)
    if total_migrated:
        print(f"Migration complete: {total_migrated} photo(s) moved to SQLite.")
        print()
        print("You may now delete the data/fault_photos/ directory once you have")
        print("verified that all photos appear correctly in the application.")
    else:
        print("No new photos to migrate.")


if __name__ == "__main__":
    main()
