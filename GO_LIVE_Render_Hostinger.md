# Go live: Render (free) + your Hostinger domain

A single linear checklist. Replace `denovovhh-db.com` with your actual domain
everywhere below. Expect ~20-30 minutes end to end (most of it waiting for the
first build and for DNS to propagate).

---

## Step 1 — Put the code on GitHub

Render deploys from a Git repo. The bundle includes a 60 MB database file, which
is **too big for GitHub's browser "Upload files" button (25 MB limit)** — so use
`git` on the command line or the GitHub Desktop app. 60 MB is fine over git
(GitHub's hard limit is 100 MB per file).

1. Create a new **empty** repo at https://github.com/new — name it e.g.
   `denovovhh-db`, keep it Public or Private (either works with Render), and do
   NOT add a README/.gitignore (the bundle already has files).
2. On your computer, unzip this bundle, open a terminal in the `denovovhh_db`
   folder, and run:

   ```bash
   git init
   git add .
   git commit -m "DeNovoVHH-DB v1.0"
   git branch -M main
   git remote add origin https://github.com/<your-username>/denovovhh-db.git
   git push -u origin main
   ```

   (GitHub Desktop: File > Add Local Repository > select the folder >
   Publish repository. It handles the 60 MB file the same way.)

---

## Step 2 — Deploy on Render

1. Sign up / log in at https://render.com (use "Sign in with GitHub" so it can
   see your repo).
2. Dashboard > **New +** > **Blueprint**.
3. Select your `denovovhh-db` repo. Render reads `render.yaml` and proposes a
   **free** web service named `denovovhh-db` in Singapore. Click **Apply**.
4. First build takes ~5-8 minutes (installing pandas/biopython, copying the DB).
   When it finishes you get a live URL like `denovovhh-db.onrender.com` — open it
   and confirm the site works (try the search and the `/docs` API page).

   *No `render.yaml`?* Use **New + > Web Service** instead, pick the repo, set
   Runtime = **Docker**, Instance = **Free**, Region = **Singapore**, Health
   Check Path = `/`, then Create.

---

## Step 3 — Attach your Hostinger domain

1. In Render: your service > **Settings** > **Custom Domains** > **Add Custom
   Domain**. Add both:
   - `denovovhh-db.com`   (your root/apex domain)
   - `www.denovovhh-db.com`
2. Render shows the **exact DNS records** to create — usually:
   - an **A record** for the apex `@` pointing to a Render IP (e.g. `216.24.57.1`)
   - a **CNAME** for `www` pointing to `denovovhh-db.onrender.com`

   **Use the exact values Render displays** (the IP can differ) — don't copy the
   example above blindly.

---

## Step 4 — Add those records at Hostinger

1. Hostinger **hPanel** > **Domains** > your domain > **DNS / Nameservers** >
   **DNS records**.
2. Add exactly what Render showed:
   - Type `A`, Name `@`, Points to `<the IP Render gave>`, TTL default.
   - Type `CNAME`, Name `www`, Points to `denovovhh-db.onrender.com`, TTL default.
3. If Hostinger already has default `A`/`CNAME` records on `@` or `www` (e.g.
   pointing at their parking page), **edit/delete those** so they don't conflict.
4. Save. DNS usually propagates in minutes (can take up to a few hours).

Back in Render, the custom domains flip to **Verified** once DNS resolves, and
Render auto-issues a free HTTPS certificate. Your site is then live at
`https://denovovhh-db.com`.

---

## Notes

- **Free-tier sleep:** after 15 minutes with no visitors the app sleeps; the next
  visit wakes it in ~30 seconds, then it's fast again. To remove this, upgrade the
  service to **Starter ($7/mo)** in Render (Settings > Instance Type) — no code
  change needed.
- **Updating the site later:** change files locally, `git commit`, `git push` —
  Render rebuilds and redeploys automatically (`autoDeploy: true`).
- **Optional — put Cloudflare in front:** if you later want CDN caching + DDoS
  protection, add the domain to a free Cloudflare account and switch Hostinger's
  nameservers to Cloudflare's. Not required; Render already provides HTTPS.
- Your Hostinger "unlimited" shared hosting isn't used by this app; you can point
  it at a simple landing page or ignore it.
