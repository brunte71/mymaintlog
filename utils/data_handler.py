import pandas as pd
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

class DataHandler:

    """Handle CSV data storage and retrieval for service management."""
    OBJECT_TYPES = ["Vehicle", "Facility", "Other"]
    # ...existing code...

    def update_fault_report(self, fault_id, **kwargs):
        """Update a fault report by fault_id. kwargs keys must match column names."""
        df = self._read_df_locked(self.fault_reports_file)
        mask = df["fault_id"] == fault_id
        if mask.any():
            for key, value in kwargs.items():
                if key in df.columns:
                    df.loc[mask, key] = value
            self._write_df_atomic(self.fault_reports_file, df)
            return True
        return False

    def _initialize_files(self):
        # ...existing code...
        # Fault Reports CSV
        self.fault_reports_file = DATA_DIR / "fault_reports.csv"
        if not self.fault_reports_file.exists():
            fault_reports_df = pd.DataFrame(columns=[
                "fault_id", "object_id", "object_type", "observation_date", "actual_meter_reading", "meter_unit", "description", "photo_paths", "created_date"
            ])
            self._write_df_atomic(self.fault_reports_file, fault_reports_df)

    def get_fault_reports(self, object_type=None, object_id=None):
        df = self._read_df_locked(self.fault_reports_file)
        if object_type:
            df = df[df["object_type"] == object_type]
        if object_id:
            df = df[df["object_id"] == object_id]
        return df

    def add_fault_report(self, object_id, object_type, observation_date, actual_meter_reading, meter_unit, description, photo_paths=None):
        df = self._read_df_locked(self.fault_reports_file)
        fault_id = f"FLT-{len(df) + 1:05d}"
        new_row = pd.DataFrame([{
            "fault_id": fault_id,
            "object_id": object_id,
            "object_type": object_type,
            "observation_date": observation_date,
            "actual_meter_reading": actual_meter_reading,
            "meter_unit": meter_unit,
            "description": description,
            "photo_paths": ";".join(photo_paths) if photo_paths else "",
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        self._write_df_atomic(self.fault_reports_file, df)
        return fault_id
    # ...existing code...
    # Mapping of common variants to canonical object_type values
    _OBJECT_TYPE_CANON = {
        "vehicle": "Vehicle",
        "vehicles": "Vehicle",
        "veh": "Vehicle",
        "facility": "Facility",
        "facilities": "Facility",
        "fac": "Facility",
        "other": "Other",
        "equipment": "Other",
    }
    
    def __init__(self):
        self.objects_file = DATA_DIR / "objects.csv"
        self.services_file = DATA_DIR / "services.csv"
        self.reminders_file = DATA_DIR / "reminders.csv"
        self.reports_file = DATA_DIR / "reports.csv"
        self.fault_reports_file = DATA_DIR / "fault_reports.csv"
        self._initialize_files()
        try:
            from filelock import FileLock
            self._FileLock = FileLock
        except Exception:
            self._FileLock = None
    
    def _initialize_files(self):
        """Initialize CSV files if they don't exist."""
        # Objects CSV
        if not self.objects_file.exists():
            objects_df = pd.DataFrame(columns=[
                "object_id", "object_type", "name", "description", 
                "status", "created_date", "last_updated"
            ])
            self._write_df_atomic(self.objects_file, objects_df)
        
        # Services CSV
        if not self.services_file.exists():
            services_df = pd.DataFrame(columns=[
                "service_id", "object_id", "object_type", "service_name", 
                "description", "interval_days", "last_service_date", 
                "next_service_date", "status", "notes", "created_date",
                # Metering fields
                "expected_meter_reading", "meter_unit"
            ])
            self._write_df_atomic(self.services_file, services_df)
        
        # Reminders CSV
        if not self.reminders_file.exists():
            reminders_df = pd.DataFrame(columns=[
                "reminder_id", "service_id", "object_id", "object_type",
                "reminder_date", "status", "notes", "created_date"
            ])
            self._write_df_atomic(self.reminders_file, reminders_df)
        
        # Reports CSV
        if not self.reports_file.exists():
            reports_df = pd.DataFrame(columns=[
                "report_id", "object_id", "object_type", "report_type",
                "title", "description", "completion_date", "notes", "created_date",
                # Metering fields for reports (actual readings)
                "actual_meter_reading", "meter_unit"
            ])
            self._write_df_atomic(self.reports_file, reports_df)

        # Meter units list file
        self.meter_units_file = DATA_DIR / "meter_units.csv"
        if not self.meter_units_file.exists():
            mu_df = pd.DataFrame({"unit": ["km", "kWh"]})
            self._write_df_atomic(self.meter_units_file, mu_df)
    
    # ===== OBJECTS MANAGEMENT =====
    def get_objects(self, object_type=None):
        """Get all objects or filtered by type."""
        df = self._read_df_locked(self.objects_file)
        if object_type:
            df = df[df["object_type"] == object_type]
        return df
    
    def add_object(self, object_type, name, description="", status="Active"):
        """Add a new object."""
        # normalize object_type before creating
        object_type = self.normalize_object_type(object_type)
        df = self._read_df_locked(self.objects_file)
        # Prefix based on first three characters of canonical object_type
        prefix = str(object_type)[:3].upper()
        # Find existing highest index for this object_type
        existing = df[df["object_type"] == object_type]
        next_index = 1
        if not existing.empty and "object_id" in existing.columns:
            # extract numeric suffix after last '-' and compute max
            import re
            nums = []
            for oid in existing["object_id"].dropna().astype(str).tolist():
                m = re.search(r"-(\d+)$", oid)
                if m:
                    try:
                        nums.append(int(m.group(1)))
                    except Exception:
                        pass
            if nums:
                next_index = max(nums) + 1
        object_id = f"{prefix}-{next_index:04d}"
        new_row = pd.DataFrame([{
            "object_id": object_id,
            "object_type": object_type,
            "name": name,
            "description": description,
            "status": status,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        self._write_df_atomic(self.objects_file, df)
        return object_id
    
    def update_object(self, object_id, **kwargs):
        """Update an object."""
        df = self._read_df_locked(self.objects_file)
        mask = df["object_id"] == object_id
        if mask.any():
            for key, value in kwargs.items():
                if key in df.columns:
                    if key == "object_type":
                        value = self.normalize_object_type(value)
                    df.loc[mask, key] = value
            df.loc[mask, "last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._write_df_atomic(self.objects_file, df)
            return True
        return False
    
    def delete_object(self, object_id):
        """Delete an object."""
        df = self._read_df_locked(self.objects_file)
        df = df[df["object_id"] != object_id]
        self._write_df_atomic(self.objects_file, df)
    
    # ===== SERVICES MANAGEMENT =====
    def get_services(self, object_type=None, object_id=None):
        """Get services filtered by type and/or object."""
        df = self._read_df_locked(self.services_file)
        if object_type:
            df = df[df["object_type"] == object_type]
        if object_id:
            df = df[df["object_id"] == object_id]
        return df
    
    def add_service(self, object_id, object_type, service_name, interval_days, 
                   description="", status="Scheduled", notes="",
                   expected_meter_reading=None, meter_unit=None):
        """Add a new service."""
        # normalize object_type
        object_type = self.normalize_object_type(object_type)
        df = self._read_df_locked(self.services_file)
        service_id = f"SVC-{len(df) + 1:05d}"
        new_row = pd.DataFrame([{
            "service_id": service_id,
            "object_id": object_id,
            "object_type": object_type,
            "service_name": service_name,
            "description": description,
            "interval_days": interval_days,
            "last_service_date": None,
            "next_service_date": datetime.now().strftime("%Y-%m-%d"),
            "status": status,
            "notes": notes,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expected_meter_reading": expected_meter_reading,
            "meter_unit": meter_unit
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        self._write_df_atomic(self.services_file, df)
        return service_id
    
    def update_service(self, service_id, **kwargs):
        """Update a service."""
        df = self._read_df_locked(self.services_file)
        mask = df["service_id"] == service_id
        if mask.any():
            for key, value in kwargs.items():
                if key in df.columns:
                    if key == "object_type":
                        value = self.normalize_object_type(value)
                    df.loc[mask, key] = value
            self._write_df_atomic(self.services_file, df)
            return True
        return False

    # ===== METER UNIT MANAGEMENT =====
    def get_meter_units(self):
        """Return list of configured meter units."""
        if not hasattr(self, 'meter_units_file'):
            self.meter_units_file = DATA_DIR / "meter_units.csv"
        if not self.meter_units_file.exists():
            return ["km", "kWh"]
        df = pd.read_csv(self.meter_units_file)
        if 'unit' in df.columns:
            return df['unit'].dropna().astype(str).tolist()
        return []

    def add_meter_unit(self, unit):
        """Add a new meter unit if not present."""
        unit = str(unit).strip()
        if not unit:
            return False
        units = self.get_meter_units()
        if unit in units:
            return False
        units.append(unit)
        df = pd.DataFrame({"unit": units})
        self._write_df_atomic(self.meter_units_file, df)
        return True

    def delete_meter_unit(self, unit):
        """Delete a meter unit if it exists."""
        units = self.get_meter_units()
        if unit not in units:
            return False
        units = [u for u in units if u != unit]
        df = pd.DataFrame({"unit": units})
        self._write_df_atomic(self.meter_units_file, df)
        return True
    
    def delete_service(self, service_id):
        """Delete a service."""
        df = self._read_df_locked(self.services_file)
        df = df[df["service_id"] != service_id]
        self._write_df_atomic(self.services_file, df)
    
    # ===== REMINDERS MANAGEMENT =====
    def get_reminders(self, object_type=None, object_id=None, status=None):
        """Get reminders filtered by criteria."""
        df = self._read_df_locked(self.reminders_file)
        if object_type:
            df = df[df["object_type"] == object_type]
        if object_id:
            df = df[df["object_id"] == object_id]
        if status:
            df = df[df["status"] == status]
        return df
    
    def add_reminder(self, service_id, object_id, object_type, reminder_date, notes=""):
        """Add a new reminder."""
        # normalize object_type
        object_type = self.normalize_object_type(object_type)
        df = self._read_df_locked(self.reminders_file)
        reminder_id = f"REM-{len(df) + 1:05d}"
        new_row = pd.DataFrame([{
            "reminder_id": reminder_id,
            "service_id": service_id,
            "object_id": object_id,
            "object_type": object_type,
            "reminder_date": reminder_date,
            "status": "Pending",
            "notes": notes,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        self._write_df_atomic(self.reminders_file, df)
        return reminder_id
    
    def update_reminder(self, reminder_id, **kwargs):
        """Update a reminder."""
        df = self._read_df_locked(self.reminders_file)
        mask = df["reminder_id"] == reminder_id
        if mask.any():
            for key, value in kwargs.items():
                if key in df.columns:
                    if key == "object_type":
                        value = self.normalize_object_type(value)
                    df.loc[mask, key] = value
            self._write_df_atomic(self.reminders_file, df)
            return True
        return False

    def delete_reminder(self, reminder_id):
        """Delete a reminder safely using the locked atomic writer."""
        df = self._read_df_locked(self.reminders_file)
        if df.empty:
            return False
        df = df[df["reminder_id"] != reminder_id]
        self._write_df_atomic(self.reminders_file, df)
        return True
    
    # ===== REPORTS MANAGEMENT =====
    def get_reports(self, object_type=None, object_id=None):
        """Get reports filtered by criteria."""
        df = self._read_df_locked(self.reports_file)
        if object_type:
            df = df[df["object_type"] == object_type]
        if object_id:
            df = df[df["object_id"] == object_id]
        return df
    
    def add_report(self, object_id, object_type, report_type, title, 
                  description="", completion_date=None, notes="",
                  actual_meter_reading=None, meter_unit=None):
        """Add a new report."""
        # normalize object_type
        object_type = self.normalize_object_type(object_type)
        df = self._read_df_locked(self.reports_file)
        report_id = f"REP-{len(df) + 1:05d}"
        new_row = pd.DataFrame([{
            "report_id": report_id,
            "object_id": object_id,
            "object_type": object_type,
            "report_type": report_type,
            "title": title,
            "description": description,
            "completion_date": completion_date or datetime.now().strftime("%Y-%m-%d"),
            "notes": notes,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actual_meter_reading": actual_meter_reading,
            "meter_unit": meter_unit
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        self._write_df_atomic(self.reports_file, df)
        return report_id
    
    def update_report(self, report_id, **kwargs):
        """Update a report."""
        df = self._read_df_locked(self.reports_file)
        mask = df["report_id"] == report_id
        if mask.any():
            for key, value in kwargs.items():
                if key in df.columns:
                    if key == "object_type":
                        value = self.normalize_object_type(value)
                    df.loc[mask, key] = value
            self._write_df_atomic(self.reports_file, df)

    def _get_lock(self, target_path: Path):
        if self._FileLock:
            return self._FileLock(str(target_path) + ".lock")
        # Fallback dummy lock
        class _DummyLock:
            def __enter__(self):
                return None
            def __exit__(self, exc_type, exc, tb):
                return False
        return _DummyLock()

    def normalize_object_type(self, value):
        """Normalize a raw object_type value to a canonical one.

        Returns the canonical string if recognized, otherwise returns the
        input unchanged.
        """
        if value is None:
            return value
        v = str(value).strip()
        key = v.lower()
        return self._OBJECT_TYPE_CANON.get(key, v)

    def _read_df_locked(self, target_path: Path):
        """Read a CSV under a file lock. Returns empty DataFrame if missing."""
        if not target_path.exists():
            return pd.DataFrame()
        with self._get_lock(target_path):
            df = pd.read_csv(target_path)
            # Normalize object_type values on read to canonical forms
            if "object_type" in df.columns:
                df = df.copy()
                df["object_type"] = df["object_type"].apply(self.normalize_object_type)
            return df
    def _write_df_atomic(self, target_path: Path, df):
        """Write a DataFrame atomically to `target_path`.

        This writes to a temp file on the same filesystem and then replaces
        the target, minimizing the risk of data loss if the process is
        interrupted. It also attempts to fsync the file and directory.
        """
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create temp file in same directory to ensure os.replace is atomic
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=str(target_dir))
        os.close(fd)
        try:
            # Use pandas to write to the temporary path
            df.to_csv(tmp_path, index=False)

            # Ensure data is flushed to disk
            with open(tmp_path, "rb+") as f:
                f.flush()
                os.fsync(f.fileno())

            # Atomically replace
            os.replace(tmp_path, str(target_path))

            # Try to fsync the directory to ensure the rename is persisted
            try:
                dir_fd = os.open(str(target_dir), os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except Exception:
                # Not critical; continue
                pass
        finally:
            # Cleanup temp if it still exists
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            return True
        return False
    
    def delete_report(self, report_id):
        """Delete a report."""
        df = self._read_df_locked(self.reports_file)
        if df.empty:
            return False
        df = df[df["report_id"] != report_id]
        self._write_df_atomic(self.reports_file, df)
        return True
