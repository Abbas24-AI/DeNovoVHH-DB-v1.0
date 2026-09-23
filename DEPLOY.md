# Deploying DeNovoVHH-DB

A FastAPI app (uvicorn) with a **read-only 60 MB SQLite release** baked in. No
database server, no user writes, no persistent storage needed — one container
plus the bundled file. This makes it cheap and simple to host.

**Cloudflare is the front door, not the server.** In every option below,
Cloudflare provides your domain, free HTTPS, CDN caching, and DDoS protection;
a separate host runs the Python process.

---

## 0. Test locally first

```bash
docker build -t denovovhh-db .
docker run --rm -p 8000:8000 denovovhh-db
# open http://localhost:8000   (API docs at /docs)
```

If that works, every deployment target below runs the identical image.

---

## 1. Domain (Cloudflare Registrar) — recommended

1. Cloudflare dashboard → **Domain Registration → Register Domains**.
2. Search a name (e.g. `denovovhh-db.org`) and buy it (~$10/yr, at-cost, free
   WHOIS privacy). The zone is added to your account automatically.
3. DNS records get set in the option you pick below.

*Free alternative:* ask **Sunway IT** for a `denovovhh-db.sunway.edu.my`
subdomain and a CNAME to your host — institutional credibility, no cost.

---

## 2. Hosting — pick ONE

### Option A — Render  (recommended: least maintenance)

1. Push this folder to a GitHub repo.
2. Render dashboard → **New → Blueprint**, select the repo. `render.yaml` is
   detected; it creates an always-on **Starter ($7/mo)** web service in
   Singapore. (Set `plan: free` for a demo that sleeps after 15 min idle.)
3. After it goes live at `denovovhh-db.onrender.com`, add your domain:
   Render service → **Settings → Custom Domains** → add `denovovhh-db.org`.
4. In Cloudflare DNS, add the record Render shows you:
   - `CNAME  @  denovovhh-db.onrender.com`  (proxied — orange cloud on)
   - `CNAME  www  denovovhh-db.onrender.com`  (proxied)
5. Cloudflare SSL/TLS mode → **Full**. Done.

### Option B — Fly.io  (cheaper always-on, CLI-driven)

```bash
curl -L https://fly.io/install.sh | sh    # install flyctl
fly auth login
fly launch --no-deploy                     # keep the bundled fly.toml
fly deploy
fly certs add denovovhh-db.org             # prints the DNS record to create
```
Then in Cloudflare DNS add the `CNAME @ denovovhh-db.fly.dev` (proxied) and set
SSL/TLS → **Full**. Set `min_machines_running = 1` in `fly.toml` for no cold
starts (~$3–4/mo), or leave 0 to scale to zero when idle.

### Option C — VPS (Hostinger KVM / Hetzner / DigitalOcean)

Works on any VPS with Docker. **Hostinger:** buy a **KVM VPS** plan (NOT shared/
web hosting — shared hosting cannot run a persistent Python ASGI process),
choose Ubuntu 22.04 with the Docker template.

```bash
# on the server
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
git clone <your-repo> denovovhh-db && cd denovovhh-db
docker compose up -d --build          # app now on 127.0.0.1:8000
```

The app is bound to localhost only. Expose it via **Cloudflare Tunnel** (no open
ports — recommended):

```bash
# install cloudflared, then:
cloudflared login
cloudflared tunnel create denovovhh-db
cloudflared tunnel route dns denovovhh-db denovovhh-db.org
# edit cloudflared/config.example.yml with your tunnel UUID -> /etc/cloudflared/config.yml
sudo cloudflared service install && sudo systemctl start cloudflared
```

The tunnel creates the DNS record for you and provides HTTPS end-to-end. No
firewall changes, no public IP exposure.

*(Alternative to the tunnel: run Caddy/nginx on the VPS to terminate TLS on
port 443 and point Cloudflare DNS `A @ <server-ip>` proxied. The tunnel is
simpler and safer.)*

---

## 3. Tuning & notes

- **Workers:** `WEB_CONCURRENCY` env var (default 1). 2 is plenty for academic
  traffic; each worker adds ~150–250 MB RAM (pandas/biopython), so keep the
  instance ≥ 512 MB.
- **The DB is read-only** — safe to run multiple workers and multiple instances
  behind a load balancer; nothing to sync.
- **Updating the data:** rebuild the image with a new `data/denovovhh.sqlite`
  and redeploy. There is no live database to migrate.
- **PostgreSQL (optional):** the schema is portable. Set `DENOVOVHH_DB_URL` to a
  `postgresql+psycopg://...` URL to run the identical app on Postgres instead of
  the bundled SQLite.
- **Health check path** is `/` (returns the home page, HTTP 200).

## Cost summary

| Setup | Monthly | Notes |
|---|---|---|
| Render Starter + Cloudflare .org | ~$7 + $10/yr | least maintenance |
| Fly.io always-on + .org | ~$3–4 + $10/yr | cheaper, CLI |
| Hostinger/Hetzner VPS + Tunnel | ~$5–8 + $10/yr | full control, you admin it |
| Render free + .org | $10/yr only | sleeps when idle (demo) |
