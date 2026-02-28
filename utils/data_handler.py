"""DataHandler – SQLite backend for mymaintlog.

Replaces the original CSV + filelock implementation.  The public API is
identical so no page code needs to change, except for two places that
previously accessed private CSV internals and now use dedicated methods:
  - delete_fault_report()  (replaces direct _write_df_atomic call in Fault Reports page)
  - delete_user_data()     (replaces the CSV loop in Admin Panel page)
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "mymaintlog.db"

# Backward compatibility: if the new database file doesn't exist yet but the
# legacy "servicemgr.db" does, keep using the legacy path so existing
# deployments are not silently reset to an empty database.
_LEGACY_DB_PATH = DATA_DIR / "servicemgr.db"
if not DB_PATH.exists() and _LEGACY_DB_PATH.exists():
    DB_PATH = _LEGACY_DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS objects (
    object_id    TEXT PRIMARY KEY,
    object_type  TEXT NOT NULL,
    name         TEXT NOT NULL,
    description  TEXT DEFAULT '',
    status       TEXT DEFAULT 'Active',
    created_date TEXT,
    last_updated TEXT,
    user_email   TEXT
);
CREATE TABLE IF NOT EXISTS services (
    service_id             TEXT PRIMARY KEY,
    object_id              TEXT,
    object_type            TEXT,
    service_name           TEXT,
    description            TEXT DEFAULT '',
    interval_days          INTEGER,
    last_service_date      TEXT,
    next_service_date      TEXT,
    status                 TEXT DEFAULT 'Scheduled',
    notes                  TEXT DEFAULT '',
    created_date           TEXT,
    expected_meter_reading REAL,
    meter_unit             TEXT,
    user_email             TEXT
);
CREATE TABLE IF NOT EXISTS reminders (
    reminder_id        TEXT PRIMARY KEY,
    service_id         TEXT,
    object_id          TEXT,
    object_type        TEXT,
    reminder_date      TEXT,
    status             TEXT DEFAULT 'Pending',
    notes              TEXT DEFAULT '',
    created_date       TEXT,
    user_email         TEXT,
    email_notification INTEGER DEFAULT 0,
    notification_time  TEXT DEFAULT '09:00',
    email_sent         INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reports (
    report_id            TEXT PRIMARY KEY,
    object_id            TEXT,
    object_type          TEXT,
    report_type          TEXT,
    title                TEXT,
    description          TEXT DEFAULT '',
    completion_date      TEXT,
    notes                TEXT DEFAULT '',
    created_date         TEXT,
    actual_meter_reading REAL,
    meter_unit           TEXT,
    user_email           TEXT
);
CREATE TABLE IF NOT EXISTS fault_reports (
    fault_id             TEXT PRIMARY KEY,
    object_id            TEXT,
    object_type          TEXT,
    observation_date     TEXT,
    actual_meter_reading REAL,
    meter_unit           TEXT,
    description          TEXT,
    photo_paths          TEXT DEFAULT '',
    created_date         TEXT,
    user_email           TEXT
);
CREATE TABLE IF NOT EXISTS meter_units (
    unit TEXT PRIMARY KEY
);
"""

# Valid columns per table – used to silently ignore unknown kwargs in
# update_* methods (same protection the original code had via `if key in df.columns`).
_TABLE_COLUMNS = {
    "objects": frozenset([
        "object_id", "object_type", "name", "description",
        "status", "created_date", "last_updated", "user_email",
    ]),
    "services": frozenset([
        "service_id", "object_id", "object_type", "service_name",
        "description", "interval_days", "last_service_date",
        "next_service_date", "status", "notes", "created_date",
        "expected_meter_reading", "meter_unit", "user_email",
    ]),
    "reminders": frozenset([
        "reminder_id", "service_id", "object_id", "object_type",
        "reminder_date", "status", "notes", "created_date",
        "user_email", "email_notification", "notification_time", "email_sent",
    ]),
    "reports": frozenset([
        "report_id", "object_id", "object_type", "report_type",
        "title", "description", "completion_date", "notes",
        "created_date", "actual_meter_reading", "meter_unit", "user_email",
    ]),
    "fault_reports": frozenset([
        "fault_id", "object_id", "object_type", "observation_date",
        "actual_meter_reading", "meter_unit", "description",
        "photo_paths", "created_date", "user_email",
    ]),
}


class DataHandler:
    """Handle SQLite data storage and retrieval for service management."""

    OBJECT_TYPES = ["Vehicle", "Facility", "Other"]

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

    def __init__(self, db_path=None):
        self._db_path = db_path or str(DB_PATH)
        self._initialize_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_conn(self):
        """Open a connection with WAL mode for safe concurrent access.

        check_same_thread=False is required because Streamlit may call
        DataHandler methods from a different thread than the one that
        constructed the object.  Each method call creates its own
        connection (opened and closed via the context manager), so no
        single Connection object is ever shared between threads.
        """
        conn = sqlite3.connect(self._db_path, timeout=30, check_same_thread=False)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous  = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize_db(self):
        """Create tables and seed meter_units on first run."""
        with self._get_conn() as conn:
            conn.executescript(_SCHEMA)
            if not conn.execute("SELECT 1 FROM meter_units LIMIT 1").fetchone():
                conn.executemany(
                    "INSERT OR IGNORE INTO meter_units (unit) VALUES (?)",
                    [("km",), ("kWh",)],
                )

    @staticmethod
    def _where(clauses):
        return ("WHERE " + " AND ".join(clauses)) if clauses else ""

    def _norm_df(self, df):
        """Return a copy of *df* with object_type column normalised."""
        if "object_type" in df.columns and not df.empty:
            df = df.copy()
            df["object_type"] = df["object_type"].apply(self.normalize_object_type)
        return df

    def normalize_object_type(self, value):
        """Normalise a raw object_type value to its canonical form."""
        if value is None:
            return value
        v = str(value).strip()
        return self._OBJECT_TYPE_CANON.get(v.lower(), v)

    # ------------------------------------------------------------------
    # Objects
    # ------------------------------------------------------------------

    def get_objects(self, object_type=None, user_email=None, is_admin=False):
        """Get all objects or filtered by type and user."""
        clauses, params = [], []
        if object_type:
            clauses.append("object_type = ?")
            params.append(self.normalize_object_type(object_type))
        if user_email and not is_admin:
            clauses.append("user_email = ?")
            params.append(user_email)
        sql = f"SELECT * FROM objects {self._where(clauses)}"
        with self._get_conn() as conn:
            df = pd.read_sql_query(sql, conn, params=params)
        return self._norm_df(df)

    def add_object(self, object_type, name, description="", status="Active", user_email=None):
        """Add a new object."""
        object_type = self.normalize_object_type(object_type)
        prefix = str(object_type)[:3].upper()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT MAX(CAST(SUBSTR(object_id, 5) AS INTEGER)) "
                "FROM objects WHERE object_type = ?",
                (object_type,),
            ).fetchone()
            object_id = f"{prefix}-{(row[0] or 0) + 1:04d}"
            conn.execute(
                "INSERT INTO objects VALUES (?,?,?,?,?,?,?,?)",
                (object_id, object_type, name, description, status, now, now, user_email),
            )
        return object_id

    def update_object(self, object_id, **kwargs):
        """Update an object."""
        # Column names are validated against the known-column frozenset before
        # being interpolated into SQL, so f-string interpolation is safe here.
        valid = _TABLE_COLUMNS["objects"]
        sets, params = [], []
        for key, value in kwargs.items():
            if key not in valid:
                continue
            if key == "object_type":
                value = self.normalize_object_type(value)
            sets.append(f"{key} = ?")
            params.append(value)
        if not sets:
            return False
        sets.append("last_updated = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(object_id)
        with self._get_conn() as conn:
            cur = conn.execute(
                f"UPDATE objects SET {', '.join(sets)} WHERE object_id = ?", params
            )
        return cur.rowcount > 0

    def delete_object(self, object_id):
        """Delete an object."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM objects WHERE object_id = ?", (object_id,))

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------

    def get_services(self, object_type=None, object_id=None, user_email=None, is_admin=False):
        """Get services filtered by type, object, and user."""
        clauses, params = [], []
        if object_type:
            clauses.append("object_type = ?")
            params.append(self.normalize_object_type(object_type))
        if object_id:
            clauses.append("object_id = ?")
            params.append(object_id)
        if user_email and not is_admin:
            clauses.append("user_email = ?")
            params.append(user_email)
        sql = f"SELECT * FROM services {self._where(clauses)}"
        with self._get_conn() as conn:
            df = pd.read_sql_query(sql, conn, params=params)
        return self._norm_df(df)

    def add_service(self, object_id, object_type, service_name, interval_days,
                    description="", status="Scheduled", notes="",
                    expected_meter_reading=None, meter_unit=None, user_email=None):
        """Add a new service."""
        object_type = self.normalize_object_type(object_type)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().strftime("%Y-%m-%d")
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT MAX(CAST(SUBSTR(service_id, 5) AS INTEGER)) FROM services"
            ).fetchone()
            service_id = f"SVC-{(row[0] or 0) + 1:05d}"
            conn.execute(
                "INSERT INTO services VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (service_id, object_id, object_type, service_name, description,
                 interval_days, None, today, status, notes, now,
                 expected_meter_reading, meter_unit, user_email),
            )
        return service_id

    def update_service(self, service_id, **kwargs):
        """Update a service."""
        valid = _TABLE_COLUMNS["services"]
        sets, params = [], []
        for key, value in kwargs.items():
            if key not in valid:
                continue
            if key == "object_type":
                value = self.normalize_object_type(value)
            sets.append(f"{key} = ?")
            params.append(value)
        if not sets:
            return False
        params.append(service_id)
        with self._get_conn() as conn:
            cur = conn.execute(
                f"UPDATE services SET {', '.join(sets)} WHERE service_id = ?", params
            )
        return cur.rowcount > 0

    def delete_service(self, service_id):
        """Delete a service."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM services WHERE service_id = ?", (service_id,))

    # ------------------------------------------------------------------
    # Meter units
    # ------------------------------------------------------------------

    def get_meter_units(self):
        """Return list of configured meter units."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT unit FROM meter_units ORDER BY unit").fetchall()
        return [r[0] for r in rows]

    def add_meter_unit(self, unit):
        """Add a new meter unit if not present."""
        unit = str(unit).strip()
        if not unit:
            return False
        try:
            with self._get_conn() as conn:
                conn.execute("INSERT INTO meter_units (unit) VALUES (?)", (unit,))
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_meter_unit(self, unit):
        """Delete a meter unit if it exists."""
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM meter_units WHERE unit = ?", (unit,))
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------

    def get_reminders(self, object_type=None, object_id=None, status=None,
                      user_email=None, is_admin=False):
        """Get reminders filtered by criteria and user."""
        clauses, params = [], []
        if object_type:
            clauses.append("object_type = ?")
            params.append(self.normalize_object_type(object_type))
        if object_id:
            clauses.append("object_id = ?")
            params.append(object_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if user_email and not is_admin:
            clauses.append("user_email = ?")
            params.append(user_email)
        sql = f"SELECT * FROM reminders {self._where(clauses)}"
        with self._get_conn() as conn:
            df = pd.read_sql_query(sql, conn, params=params)
        return self._norm_df(df)

    def add_reminder(self, service_id, object_id, object_type, reminder_date, notes="",
                     user_email=None, email_notification=False, notification_time="09:00"):
        """Add a new reminder."""
        object_type = self.normalize_object_type(object_type)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT MAX(CAST(SUBSTR(reminder_id, 5) AS INTEGER)) FROM reminders"
            ).fetchone()
            reminder_id = f"REM-{(row[0] or 0) + 1:05d}"
            conn.execute(
                "INSERT INTO reminders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (reminder_id, service_id, object_id, object_type, reminder_date,
                 "Pending", notes, now, user_email,
                 1 if email_notification else 0, notification_time, 0),
            )
        return reminder_id

    def update_reminder(self, reminder_id, **kwargs):
        """Update a reminder."""
        valid = _TABLE_COLUMNS["reminders"]
        sets, params = [], []
        for key, value in kwargs.items():
            if key not in valid:
                continue
            if key == "object_type":
                value = self.normalize_object_type(value)
            sets.append(f"{key} = ?")
            params.append(value)
        if not sets:
            return False
        params.append(reminder_id)
        with self._get_conn() as conn:
            cur = conn.execute(
                f"UPDATE reminders SET {', '.join(sets)} WHERE reminder_id = ?", params
            )
        return cur.rowcount > 0

    def delete_reminder(self, reminder_id):
        """Delete a reminder."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM reminders WHERE reminder_id = ?", (reminder_id,)
            )
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def get_reports(self, object_type=None, object_id=None, user_email=None, is_admin=False):
        """Get reports filtered by criteria and user."""
        clauses, params = [], []
        if object_type:
            clauses.append("object_type = ?")
            params.append(self.normalize_object_type(object_type))
        if object_id:
            clauses.append("object_id = ?")
            params.append(object_id)
        if user_email and not is_admin:
            clauses.append("user_email = ?")
            params.append(user_email)
        sql = f"SELECT * FROM reports {self._where(clauses)}"
        with self._get_conn() as conn:
            df = pd.read_sql_query(sql, conn, params=params)
        return self._norm_df(df)

    def add_report(self, object_id, object_type, report_type, title,
                   description="", completion_date=None, notes="",
                   actual_meter_reading=None, meter_unit=None, user_email=None):
        """Add a new report."""
        object_type = self.normalize_object_type(object_type)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT MAX(CAST(SUBSTR(report_id, 5) AS INTEGER)) FROM reports"
            ).fetchone()
            report_id = f"REP-{(row[0] or 0) + 1:05d}"
            conn.execute(
                "INSERT INTO reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (report_id, object_id, object_type, report_type, title, description,
                 completion_date or datetime.now().strftime("%Y-%m-%d"),
                 notes, now, actual_meter_reading, meter_unit, user_email),
            )
        return report_id

    def update_report(self, report_id, **kwargs):
        """Update a report."""
        valid = _TABLE_COLUMNS["reports"]
        sets, params = [], []
        for key, value in kwargs.items():
            if key not in valid:
                continue
            if key == "object_type":
                value = self.normalize_object_type(value)
            sets.append(f"{key} = ?")
            params.append(value)
        if not sets:
            return False
        params.append(report_id)
        with self._get_conn() as conn:
            cur = conn.execute(
                f"UPDATE reports SET {', '.join(sets)} WHERE report_id = ?", params
            )
        return cur.rowcount > 0

    def delete_report(self, report_id):
        """Delete a report."""
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM reports WHERE report_id = ?", (report_id,))
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Fault reports
    # ------------------------------------------------------------------

    def get_fault_reports(self, object_type=None, object_id=None, user_email=None, is_admin=False):
        clauses, params = [], []
        if object_type:
            clauses.append("object_type = ?")
            params.append(self.normalize_object_type(object_type))
        if object_id:
            clauses.append("object_id = ?")
            params.append(object_id)
        if user_email and not is_admin:
            clauses.append("user_email = ?")
            params.append(user_email)
        sql = f"SELECT * FROM fault_reports {self._where(clauses)}"
        with self._get_conn() as conn:
            df = pd.read_sql_query(sql, conn, params=params)
        return self._norm_df(df)

    def add_fault_report(self, object_id, object_type, observation_date,
                         actual_meter_reading, meter_unit, description,
                         photo_paths=None, user_email=None):
        object_type = self.normalize_object_type(object_type)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT MAX(CAST(SUBSTR(fault_id, 5) AS INTEGER)) FROM fault_reports"
            ).fetchone()
            fault_id = f"FLT-{(row[0] or 0) + 1:05d}"
            conn.execute(
                "INSERT INTO fault_reports VALUES (?,?,?,?,?,?,?,?,?,?)",
                (fault_id, object_id, object_type, observation_date,
                 actual_meter_reading, meter_unit, description,
                 ";".join(photo_paths) if photo_paths else "",
                 now, user_email),
            )
        return fault_id

    def update_fault_report(self, fault_id, **kwargs):
        """Update a fault report by fault_id. kwargs keys must match column names."""
        valid = _TABLE_COLUMNS["fault_reports"]
        sets, params = [], []
        for key, value in kwargs.items():
            if key not in valid:
                continue
            if key == "object_type":
                value = self.normalize_object_type(value)
            sets.append(f"{key} = ?")
            params.append(value)
        if not sets:
            return False
        params.append(fault_id)
        with self._get_conn() as conn:
            cur = conn.execute(
                f"UPDATE fault_reports SET {', '.join(sets)} WHERE fault_id = ?", params
            )
        return cur.rowcount > 0

    def delete_fault_report(self, fault_id):
        """Delete a single fault report."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM fault_reports WHERE fault_id = ?", (fault_id,)
            )
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Admin: delete all records for a user
    # ------------------------------------------------------------------

    def delete_user_data(self, user_email):
        """Delete all records belonging to *user_email* across every table."""
        # Table names are hardcoded string literals, not user input – safe to interpolate.
        with self._get_conn() as conn:
            for table in ("objects", "services", "reminders", "reports", "fault_reports"):
                conn.execute(f"DELETE FROM {table} WHERE user_email = ?", (user_email,))
