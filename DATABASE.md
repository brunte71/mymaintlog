# Database vs CSV: Analysis and Recommendation for ServiceMgr

## Does replacing CSV with a database make a difference?

**Yes — significantly.** The table below summarises the key differences.

| Concern | CSV + filelock (old) | SQLite (new) |
|---------|----------------------|--------------|
| Concurrent writes | One writer at a time (filelock) | Serialised by SQLite WAL; multiple concurrent readers |
| Data integrity | Workaround (temp-file + atomic rename) | Full ACID transactions |
| Corruption risk | Process crash can leave partial writes | WAL journal survives crashes cleanly |
| Query efficiency | Load full file into RAM, filter in pandas | Indexed SQL — filters happen before data leaves disk |
| Storage | 6 separate CSV files + lock files | 1 `.db` file |
| Backup | Copy 6+ files consistently | Single file copy or `sqlite3 .backup` |
| Cloud deployment | Needs persistent volume for all 6 CSVs | Same for SQLite; OR use a managed cloud DB to remove the volume entirely |
| Cost | Free | Free (SQLite) or free tier (managed Postgres) |

---

## Recommended database: SQLite (already implemented)

SQLite is the right choice for ServiceMgr because:

- **Zero cost** – part of Python's standard library; no server, no subscription.
- **Zero configuration** – no installation, no connection strings.
- **Drop-in replacement** – the entire public API of `DataHandler` is unchanged; no page code required modification.
- **Single file** – `data/servicemgr.db` replaces six CSV files and their lock files.
- **WAL mode** – write-ahead logging allows simultaneous reads while a write is in progress, which is ideal for Streamlit's multi-thread model.
- **Widely supported** – every cloud platform, Docker image and CI runner already has SQLite.

### Files changed

| File | Change |
|------|--------|
| `utils/data_handler.py` | Full rewrite: CSV → SQLite (`sqlite3` stdlib) |
| `pages/2_Fault_Reports.py` | Use new `delete_fault_report()` instead of internal CSV writer |
| `pages/99_Admin_Panel.py` | Use new `delete_user_data()` instead of CSV loop |
| `requirements.txt` | Removed `filelock` (no longer needed) |
| `scripts/migrate_csv_to_sqlite.py` | **New** – one-time import of existing CSV data |
| `scripts/migrate_object_types.py` | Updated to work against SQLite |

### Migration from CSV

If you already have CSV data, run once:

```bash
python scripts/migrate_csv_to_sqlite.py
```

The script reads all existing CSV files and imports their rows into the SQLite
database, skipping any rows whose primary key is already present (safe to run
multiple times).

---

## Alternative: PostgreSQL on Supabase or Neon (free, managed)

Using a **managed cloud PostgreSQL** database instead of SQLite unlocks one
important extra benefit: the app no longer needs a persistent volume at all,
which means it can run on **Streamlit Community Cloud for free** (fully free,
no Fly.io account needed).

### Free-tier comparison

| Provider | Free storage | Connection limit | Notes |
|----------|-------------|-----------------|-------|
| **Supabase** | 500 MB | 60 | Postgres 15, REST API, auth |
| **Neon** | 512 MB (0.5 GB) | 100 | Serverless Postgres, auto-suspend |
| **PlanetScale** | ❌ | — | Free tier discontinued April 2024 |
| **ElephantSQL** (Tiny Turtle) | 20 MB | 5 | Small but sufficient for this app |

500 MB of Postgres storage holds tens of thousands of service records –
far more than a typical fleet maintenance application ever generates.

### Required code change for PostgreSQL

Switching `DataHandler` from SQLite to PostgreSQL requires:

1. Install `psycopg2-binary` (add to `requirements.txt`).
2. Replace `sqlite3.connect(...)` with a `psycopg2` connection.
3. Replace `?` parameter placeholders with `%s`.
4. Store the connection URL in `.streamlit/secrets.toml` (never in code).

A community-maintained pattern for this is available at:
https://docs.streamlit.io/develop/tutorials/databases/postgresql

### When to choose PostgreSQL over SQLite

| Scenario | SQLite | PostgreSQL |
|----------|--------|-----------|
| Single-server Docker / Fly.io deployment | ✅ Best choice | Overkill |
| Streamlit Community Cloud (free) | ❌ Ephemeral filesystem | ✅ Required |
| Multiple concurrent Streamlit workers | ⚠️ SQLite WAL handles it, but consider PG for >10 concurrent users | ✅ |
| Zero DevOps overhead | ✅ | ✅ (managed) |
| Zero monthly cost | ✅ | ✅ (within free tier) |

---

## Summary

> **SQLite is the recommended database for ServiceMgr** — it is free, requires
> no external service, and is already implemented in this repository.  It
> eliminates the file-locking complexity, reduces storage from six files to one,
> and improves resilience against data corruption.
>
> If you want to deploy on **Streamlit Community Cloud** (completely free, no
> Fly.io account), migrate `DataHandler` to use **Supabase** or **Neon**
> PostgreSQL (both have generous free tiers that comfortably fit this
> application).
