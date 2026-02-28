# Cloud Hosting Recommendations for mymaintlog

## Project Size Overview

| Asset | Size |
|-------|------|
| Python source (14 files, ~2,600 lines) | ~100 KB |
| Config & YAML files | ~5 KB |
| Sample data (SQLite DB + CSVs) | ~10 KB |
| Sample fault photos (6 photos) | ~3 MB |
| **Git repository total** | **~6.6 MB** |
| **Deployed Docker image** | **~650–750 MB** (python:3.12-slim + pandas + streamlit) |
| **Fly.io volume (initial, empty)** | **< 1 MB** |

The Docker image is large because of the pandas/streamlit dependency chain, but it is
only downloaded by Fly.io's build workers – it does **not** affect ongoing bandwidth
costs. The persistent volume (which holds your SQLite database and uploaded fault
photos) starts near-empty and grows at roughly **2–15 MB per user per year**,
dominated by fault photo uploads (~400–600 KB each).

---

## TL;DR – Cheapest Options Ranked

| Rank | Platform | Est. Annual Cost (5–20 users) | Persistent Storage | Difficulty |
|------|----------|-------------------------------|--------------------|------------|
| 🥇 1 | **Fly.io** | **$60/yr†** | ✅ Volumes (3 GB free) | Easy |
| 🥈 2 | **Streamlit Community Cloud** | **$0/yr** | ⚠️ Ephemeral\* | Easiest |
| 🥉 3 | **Railway** | **~$60/yr** | ✅ Volumes included | Easy |
| 4 | Render | ~$84/yr | ✅ Persistent disk | Easy |
| 5 | Oracle Cloud (Always Free VM) | **$0/yr** | ✅ 200 GB block | Hard |

\* Streamlit Community Cloud has an ephemeral filesystem – data resets on each
  restart unless you add an external data store (see Option 2 below).

† New Fly.io accounts require a $5/month Hobby plan ($60/year). Legacy
  "grandfathered" accounts with no monthly minimum can run this app for $0.

---

## Option 1 – Fly.io (Recommended: $60/year for up to 50 users¹)

Fly.io offers a generous free tier that covers this application end-to-end.
The app runs in a Docker container with a **persistent volume** that keeps your
SQLite database and fault photos intact across restarts and re-deployments.

### Why Fly.io fits mymaintlog
- Persistent volumes → SQLite database and uploaded photos survive restarts
- Scale-to-zero machines → $0 when the app is idle
- 3 GB persistent storage free → enough for years of data and photos
- Built-in HTTPS with automatic TLS certificates
- SMTP outbound traffic allowed (for email reminders)

### Free-tier allowances (as of 2025)
| Resource | Free allowance |
|----------|---------------|
| Shared VMs | 3 × `shared-cpu-1x` (256 MB RAM) running 24/7 |
| Persistent volumes | 3 GB total per organisation |
| Outbound bandwidth | 160 GB/month per organisation |

> **Note:** New Fly.io organisations require a **$5/month Hobby plan** (credit
> card required), giving a $60/year minimum regardless of actual resource usage.
> Legacy/"grandfathered" hobby accounts have no monthly minimum and can run this
> app for $0.  The free resource allowances (machines, volume, bandwidth) apply
> equally to both account types.

A single mymaintlog instance fits entirely within these limits.

### Step-by-step deployment

1. **Install the Fly CLI**
   ```bash
   # macOS / Linux
   curl -L https://fly.io/install.sh | sh

   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Sign up and log in** (credit card required for new Hobby plan accounts)
   ```bash
   fly auth signup   # or: fly auth login
   ```

3. **Create the app**
   ```bash
   cd /path/to/mymaintlog
   fly apps create mymaintlog   # pick a unique name
   ```

4. **Create the persistent volume** (1 GB is plenty)
   ```bash
   fly volumes create mymaintlog_data --size 1 --region ams
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Open the app**
   ```bash
   fly open
   ```

### Keeping compute costs at $0 (scale-to-zero)
Set `auto_stop_machines = true` and `min_machines_running = 0` in `fly.toml`
(already the default in the provided config). The machine starts in ~2 seconds
when a user visits and sleeps after inactivity.  This eliminates compute
charges above the Hobby plan minimum for low-traffic deployments.

### Fly.io pricing reference (2025)

| Machine type | RAM | Monthly cost |
|---|---|---|
| `shared-cpu-1x` | 256 MB | $1.94 *(covered by free allowance)* |
| `shared-cpu-1x` | 512 MB | $3.19 |
| `shared-cpu-1x` | 1 GB | $5.70 |
| `shared-cpu-2x` | 2 GB | $11.39 |
| `shared-cpu-2x` | 4 GB | $21.40 |
| `shared-cpu-4x` | 4 GB | $22.78 |
| `shared-cpu-4x` | 8 GB | $42.79 |
| Persistent volume | per GB | $0.15/GB/month *(first 3 GB free)* |
| Outbound bandwidth | per GB | $0.02/GB *(first 160 GB/month free)* |
| Dedicated IPv4 | per address | $2.00/month |

> Prices are per 30-day month and billed per second of uptime.  Machines that
> are stopped (scale-to-zero) incur no compute charge.

---

### Scaling analysis by user count

mymaintlog is a Streamlit application backed by SQLite (WAL mode).  Key
resource drivers:

- **Memory** – Streamlit base process uses ~150–200 MB; each additional
  concurrent browser session adds ~20–50 MB (DataFrames loaded per request).
- **Storage** – SQLite DB grows ~50–200 KB per user per year in records;
  fault photos are ~400–600 KB each and dominate volume usage.
- **Bandwidth** – First page load sends ~3–5 MB of Streamlit assets; ongoing
  WebSocket traffic is ~50–200 KB per page interaction; photo uploads/views
  add ~500 KB per photo.
- **Concurrency ceiling** – Streamlit runs all sessions in one process.
  A single `shared-cpu-1x` machine handles ~10–20 concurrent active sessions
  comfortably; beyond that, response times degrade without vertical scaling.

#### Cost and configuration table

| Users | Peak concurrent | Machine | Volume | Monthly cost¹ | Annual cost¹ |
|------:|----------------:|---------|--------|-------------:|------------:|
| **5** | 1–2 | `shared-cpu-1x` 256 MB, scale-to-zero | 1 GB | **$5** | **$60** |
| **20** | 3–6 | `shared-cpu-1x` 256 MB, scale-to-zero | 1 GB | **$5** | **$60** |
| **50** | 8–15 | `shared-cpu-1x` 512 MB, always-on | 2 GB | **~$8–9** | **~$96–108** |
| **100** | 15–30 | `shared-cpu-1x` 1 GB, always-on | 5 GB | **~$11–14** | **~$132–168** |
| **500** | 50–100 | `shared-cpu-2x` 4 GB, always-on | 20 GB | **~$29–32** | **~$348–384** |
| **1,000** | 100–200 | `shared-cpu-4x` 8 GB, always-on | 40 GB | **~$53–60** | **~$636–720** |
| **5,000** | 500–1,000+ | 3–5 × `shared-cpu-4x` 8 GB + managed DB | 100 GB+ | **~$175–285** | **~$2,100–3,420** |
| **>10,000** | >1,000 | Enterprise / architecture rewrite | 200 GB+ | **$500+** | **$6,000+** |

¹ Includes $5/month Hobby plan minimum for new accounts. Legacy accounts with
  no monthly minimum: subtract $60/year from each figure.  Volume and bandwidth
  overages are included in the estimates; compute is covered by free allowances
  for the 5- and 20-user tiers.

#### Scenario notes

**5–20 users** (small team / internal tool)
- The current `fly.toml` configuration works unchanged.
- 256 MB RAM is sufficient; scale-to-zero keeps the compute cost at $0.
- The entire deployment fits inside Fly.io's free resource allowances.
- The 3 GB free volume covers several years of data and photos.
- **Estimated total: $60/year** (Hobby plan minimum for new accounts; $0/year
  for legacy accounts where the monthly minimum does not apply).

**50 users** (department-level rollout)
- Upgrade RAM to 512 MB to handle 8–15 concurrent sessions without OOM errors.
- Set `min_machines_running = 1` to avoid cold-start delays.
- Storage is still well within the 3 GB free volume.
- Recommended `fly.toml` change: `memory = "512mb"`, `min_machines_running = 1`.
- **Estimated total: ~$96–108/year** (Hobby plan + 512 MB machine cost).

**100 users** (organisation-wide)
- Upgrade to 1 GB RAM for comfortable headroom.
- Volume storage may exceed the 3 GB free tier as photo uploads accumulate
  (~$0.30–0.60/month for 5 GB volume).
- SQLite in WAL mode handles this concurrency level well (concurrent reads;
  serialised writes complete in milliseconds).
- Recommended `fly.toml` change: `memory = "1gb"`, `size = "shared-cpu-1x"`,
  `min_machines_running = 1`.
- **Estimated total: ~$132–168/year.**

**500 users** (multi-site or larger organisation)
- Move to a 2-vCPU machine (`shared-cpu-2x`) to handle the CPU load from
  50–100 concurrent Streamlit sessions.
- Fault photo storage may reach 10–20 GB; budget ~$1.05–2.55/month for
  volume overages.
- Consider migrating the SQLite database to
  **Fly Postgres** (starts at ~$3.84/month for a `shared-cpu-1x` 256 MB
  instance) to decouple database from app restarts and enable future
  horizontal scaling.
- **Estimated total: ~$348–384/year.**

**1,000 users** (large organisation)
- A single `shared-cpu-4x` 8 GB machine handles this load, but Streamlit
  becomes the architectural bottleneck at this scale.  Response times under
  heavy concurrent use will degrade.
- Fly Postgres (or an external managed PostgreSQL) is **strongly recommended**
  at this scale.
- Budget for larger volume storage (~40 GB → ~$5.55/month overage).
- **Estimated total: ~$636–720/year.**

**5,000 users** (enterprise / SaaS)
- Running multiple Fly.io machines is possible, but **the SQLite-on-volume
  architecture cannot be shared across multiple machines**.  You must migrate
  to an external database (Fly Postgres, Supabase, Neon, etc.) before
  horizontal scaling.
- Streamlit is not designed for thousands of concurrent users; at this scale
  the frontend should be rebuilt as a conventional web app (React + REST/GraphQL
  API + PostgreSQL).
- **Estimated total: ~$2,100–3,420/year** (compute only; DB and CDN costs
  are additional).

**>10,000 users** (large-scale SaaS)
- Fly.io alone is not an appropriate hosting choice at this scale without
  significant architectural changes.
- Required changes: rewrite frontend (React/Vue), add an API layer
  (FastAPI/Django), managed PostgreSQL cluster, object storage for photos
  (Cloudflare R2 / Backblaze B2), CDN, and a load balancer.
- **Estimated total: $500+/month ($6,000+/year)** before engineering costs.

#### Summary: price-based limitations

| Limitation | Threshold | Mitigation |
|---|---|---|
| 256 MB RAM exhausted | ~10–15 concurrent users | Upgrade to 512 MB–1 GB machine |
| Free 3 GB volume full | ~200–500 fault photos accumulated | Increase volume size ($0.15/GB/month) |
| Single SQLite writer | ~100+ simultaneous writes | Enable WAL mode *(already on)* or migrate to Postgres |
| Single-machine Streamlit | ~100–200 concurrent sessions | Vertical scale first; then architectural rewrite |
| Fly.io Hobby plan minimum | Any new account | $5/month ($60/year) fixed cost; free resource allowances offset compute charges |

---

### Email (SMTP reminders)
No extra infrastructure needed. Configure `email_config.yaml` with any
standard SMTP credentials (Gmail App Password, SendGrid free tier, etc.) –
Fly.io allows outbound SMTP.

---

## Option 2 – Streamlit Community Cloud ($0/year)

Streamlit Community Cloud is the easiest way to share a Streamlit app and is
completely free.

**With the SQLite backend** (now the default) the filesystem is still
ephemeral, so data is lost on restart unless you pair Community Cloud with a
free managed PostgreSQL database (Supabase or Neon – see `DATABASE.md`).
That combination gives you a **completely free, zero-ops production deployment**.

### When to use this option
- Fully free production deployment when paired with Supabase or Neon PostgreSQL
- Demo / showcase purposes with the SQLite backend (data resets on restart without an external DB)

### Making data persistent on Community Cloud
Pair the app with a free managed PostgreSQL database (Supabase or Neon).
Update `DataHandler` to use a `psycopg2` connection instead of SQLite and store
the database URL in `.streamlit/secrets.toml`.  See `DATABASE.md` for details.

### Deployment steps
1. Push the repository to GitHub (it should already be there).
2. Visit https://share.streamlit.io and click **New app**.
3. Select the repository, branch, and set the main file to `Home.py`.
4. Click **Deploy**.

### Limitation
Without an external database, uploaded photos (`data/fault_photos/`) and all
CSV/SQLite data are lost on restart.  For persistent production use, connect
to Supabase or Neon PostgreSQL as described in `DATABASE.md`.

---

## Option 3 – Railway (~$60/year)

Railway is a platform-as-a-service that supports Docker deployments with
persistent volumes out of the box. It is simple to set up and reliable.

### Pricing
- Hobby plan: **$5/month** ($60/year) – includes $5 of usage credit
- Persistent volumes: included in usage credit
- A small always-on mymaintlog instance uses roughly $2–3/month of compute,
  staying comfortably within the $5 credit.

### Deployment steps
1. Create a free account at https://railway.app.
2. Click **New Project → Deploy from GitHub repo**.
3. Select the `mymaintlog` repository. Railway auto-detects the `Dockerfile`.
4. Add a **Volume** in the service settings, mount it at `/app/data`.
5. Set the environment variable `PORT=8501` if Railway doesn't pick it up
   automatically.

---

## Option 4 – Render (~$84/year)

Render offers a managed platform with free static hosting and paid web
services.

### Pricing
- Starter web service: **$7/month** ($84/year)
- 10 GB persistent disk: **$0.25/GB/month** (~$2.50/month for 10 GB)
- Estimated total: **~$9.50/month** ($114/year)

The free tier is not recommended because it spins down after 15 minutes of
inactivity (cold-start delay of ~30–60 seconds).

### Deployment steps
1. Create an account at https://render.com.
2. Click **New → Web Service → Connect a repository**.
3. Choose the `mymaintlog` repo. Render auto-detects the `Dockerfile`.
4. Set **Start command** to: `streamlit run Home.py --server.port $PORT --server.address 0.0.0.0`
5. Add a **Persistent Disk** under the service settings, mount at `/app/data`.

---

## Option 5 – Oracle Cloud Always Free VM ($0/year)

Oracle Cloud's Always Free tier includes two AMD VMs (or one ARM VM with 4
cores / 24 GB RAM) and 200 GB of block storage – all permanently free.

### Why it is ranked last despite being free
- Requires manual Linux server administration
- You must install Docker / Python, configure systemd, set up TLS (Certbot),
  and manage OS updates yourself
- Best suited for users comfortable with Linux server management

### Rough setup steps
1. Create a free Oracle Cloud account (credit card required for identity
   verification but not charged).
2. Launch an Always Free VM (Ubuntu 22.04 LTS recommended).
3. Attach a block volume and mount it at `/opt/mymaintlog/data`.
4. Install Docker and clone the repository.
5. Run with:
   ```bash
   docker run -d \
     -p 8501:8501 \
     -v /opt/mymaintlog/data:/app/data \
     --restart unless-stopped \
     mymaintlog
   ```
6. Configure Nginx + Certbot for HTTPS.

---

## Integration Add-ons

### Email Notifications (all platforms)

| Provider | Free tier | Monthly cost |
|----------|-----------|-------------|
| Gmail SMTP (App Password) | 500 emails/day | $0 |
| SendGrid | 100 emails/day | $0 |
| Mailgun | 1,000 emails/month | $0 |
| Amazon SES | 200 emails/day (within AWS) | ~$0.10/1,000 after |

Configure the chosen provider in `email_config.yaml` – no code changes
required.

### File / Photo Storage (optional upgrade)

If photo uploads grow large, you can offload the `data/fault_photos/` folder
to object storage:

| Provider | Free tier | Cost after free tier |
|----------|-----------|----------------------|
| Backblaze B2 | 10 GB | $0.006/GB/month |
| Cloudflare R2 | 10 GB/month | $0.015/GB/month |
| AWS S3 | 5 GB (12 months) | $0.023/GB/month |

This is optional – for most organisations the Fly.io 3 GB volume is sufficient
for several years of fault photos.

---

## Summary Recommendation

> **Use Fly.io** (Option 1) for production. It is the cheapest fully-featured
> hosting option, requires **no code changes**, and handles the SQLite database
> and photo uploads out of the box.
>
> - **Up to ~20 users:** $60/year (Hobby plan minimum; $0 for legacy accounts).
> - **Up to ~100 users:** ~$132–168/year (1 GB machine, always-on + Hobby plan).
> - **Up to ~500 users:** ~$348–384/year (2-vCPU, 4 GB machine + larger volume).
> - **500–1,000+ users:** Consider migrating to Fly Postgres or an external
>   managed database; costs rise to ~$636–720+/year.
> - **5,000+ users:** Streamlit is not appropriate at this scale – the
>   application architecture needs to be re-evaluated.
>
> See the **"Scaling analysis by user count"** section above for full details.
>
> **For a completely free, zero-infrastructure deployment** use
> **Streamlit Community Cloud + Supabase/Neon PostgreSQL** (see `DATABASE.md`).
>
> All deployment configuration files are already included in this repository:
> - `Dockerfile` – container image definition
> - `fly.toml` – Fly.io app configuration (configured for ≤20 users out of the box)
> - `.streamlit/config.toml` – Streamlit production settings
> - `DATABASE.md` – database options and migration guide
