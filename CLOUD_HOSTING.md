# Cloud Hosting Recommendations for ServiceMgr

## TL;DR – Cheapest Options Ranked

| Rank | Platform | Est. Annual Cost | Persistent Storage | Difficulty |
|------|----------|------------------|--------------------|------------|
| 🥇 1 | **Fly.io** | **$0 – $36/yr** | ✅ Volumes (3 GB free) | Easy |
| 🥈 2 | **Streamlit Community Cloud** | **$0/yr** | ⚠️ Ephemeral\* | Easiest |
| 🥉 3 | **Railway** | **~$60/yr** | ✅ Volumes included | Easy |
| 4 | Render | ~$84/yr | ✅ Persistent disk | Easy |
| 5 | Oracle Cloud (Always Free VM) | **$0/yr** | ✅ 200 GB block | Hard |

\* Streamlit Community Cloud has an ephemeral filesystem – data resets on each
  restart unless you add an external data store (see Option 2 below).

---

## Option 1 – Fly.io (Recommended: ~$0–$36/year)

Fly.io offers a generous free tier that covers this application end-to-end.
The app runs in a Docker container with a **persistent volume** that keeps your
CSV data and fault photos intact across restarts and re-deployments.

### Why Fly.io fits ServiceMgr
- Persistent volumes → CSV files and uploaded photos survive restarts
- Scale-to-zero machines → $0 when the app is idle
- 3 GB persistent storage free → enough for years of CSV data and photos
- Built-in HTTPS with automatic TLS certificates
- SMTP outbound traffic allowed (for email reminders)

### Free-tier limits (as of 2025)
| Resource | Free allowance |
|----------|---------------|
| Shared VMs | 3 × `shared-cpu-1x` (256 MB RAM) |
| Persistent volumes | 3 GB total |
| Outbound bandwidth | 160 GB/month |

A single ServiceMgr instance fits entirely within these limits.

### Step-by-step deployment

1. **Install the Fly CLI**
   ```bash
   # macOS / Linux
   curl -L https://fly.io/install.sh | sh

   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Sign up and log in** (free account, no credit card required for free tier)
   ```bash
   fly auth signup   # or: fly auth login
   ```

3. **Create the app**
   ```bash
   cd /path/to/servicemgr
   fly apps create servicemgr   # pick a unique name
   ```

4. **Create the persistent volume** (1 GB is plenty)
   ```bash
   fly volumes create servicemgr_data --size 1 --region ams
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Open the app**
   ```bash
   fly open
   ```

### Keeping costs at $0
Set `auto_stop_machines = true` and `min_machines_running = 0` in `fly.toml`
(already the default in the provided config). The machine starts in ~2 seconds
when a user visits and sleeps after inactivity.

### Email (SMTP reminders)
No extra infrastructure needed. Configure `email_config.yaml` with any
standard SMTP credentials (Gmail App Password, SendGrid free tier, etc.) –
Fly.io allows outbound SMTP.

---

## Option 2 – Streamlit Community Cloud ($0/year)

Streamlit Community Cloud is the easiest way to share a Streamlit app and is
completely free. However, it uses an **ephemeral filesystem** – all data stored
in the `data/` folder is lost when the app restarts.

### When to use this option
- Demo / showcase purposes only
- Low-volume use where data loss on restart is acceptable

### Making data persistent without code changes
Mount a GitHub repository as the data backend by enabling "commit on write" –
this keeps data in a private repo branch. This approach is practical only for
very small datasets.

### Deployment steps
1. Push the repository to GitHub (it should already be there).
2. Visit https://share.streamlit.io and click **New app**.
3. Select the repository, branch, and set the main file to `Home.py`.
4. Click **Deploy**.

### Limitation
Upload photos (`data/fault_photos/`) are lost on restart. For photo-heavy use,
Fly.io (Option 1) is strongly preferred.

---

## Option 3 – Railway (~$60/year)

Railway is a platform-as-a-service that supports Docker deployments with
persistent volumes out of the box. It is simple to set up and reliable.

### Pricing
- Hobby plan: **$5/month** ($60/year) – includes $5 of usage credit
- Persistent volumes: included in usage credit
- A small always-on ServiceMgr instance uses roughly $2–3/month of compute,
  staying comfortably within the $5 credit.

### Deployment steps
1. Create a free account at https://railway.app.
2. Click **New Project → Deploy from GitHub repo**.
3. Select the `servicemgr` repository. Railway auto-detects the `Dockerfile`.
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
3. Choose the `servicemgr` repo. Render auto-detects the `Dockerfile`.
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
3. Attach a block volume and mount it at `/opt/servicemgr/data`.
4. Install Docker and clone the repository.
5. Run with:
   ```bash
   docker run -d \
     -p 8501:8501 \
     -v /opt/servicemgr/data:/app/data \
     --restart unless-stopped \
     servicemgr
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
> hosting option, requires **no code changes**, and handles persistent CSV
> storage and photo uploads out of the box. Total annual cost: **$0** within
> the free tier.
>
> All deployment configuration files are already included in this repository:
> - `Dockerfile` – container image definition
> - `fly.toml` – Fly.io app configuration
> - `.streamlit/config.toml` – Streamlit production settings
