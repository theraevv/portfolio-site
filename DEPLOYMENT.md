# Deployment Guide

## Fly.io (Recommended) — Free & Fast

Fly.io offers faster cold starts than Render, with VMs that keep running. The free tier includes 3 shared VMs with no sleep mode.

### Prerequisites
- [Install Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/)
- Sign up: `fly auth signup`
- Login: `fly auth login`

### Deploy

```bash
# Launch the app (creates fly.toml if not present)
fly launch --name portfolio-site --region iad

# Deploy
fly deploy
```

Your app will be live at `https://portfolio-site.fly.dev`.

### Update Frontend API URLs (Optional)

If you want to use Cloudflare Pages for frontend and Fly.io for backend, update fetch URLs in the HTML files:

```javascript
// From:
fetch("/api/predict/spam", ...)

// To:
fetch("https://portfolio-site.fly.dev/api/predict/spam", ...)
```

Otherwise, keep relative paths for single-domain deployment.

---

## Cloudflare Pages (Frontend Only)

For serving static HTML/CSS/JS only (no ML backend):

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → Pages
2. Create project → Connect GitHub repo
3. Framework preset: **None**
4. Build command: *(empty)*
5. Build output directory: `/`
6. Deploy

---

## Render.com (Alternative)

1. Go to [render.com](https://render.com)
2. New Web Service → Connect GitHub repo
3. Settings:
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: Free
4. Upload model files to `models/` directory via Shell tab

---

## Model Files

The following models must be present in the `models/` directory:

| File | Source |
|------|--------|
| `crop_model.pkl` | Crop Recommendation RF model |
| `diabetes_model.pkl` | Diabetes Awareness RF model |
| `mental_burn_model.pkl` | Mental Health Burnout RF model |
| `mental_dep_model.pkl` | Mental Health Depression RF model |
| `mental_anx_model.pkl` | Mental Health Anxiety RF model |
| `spam_model.pkl` | Spam/Ham Logistic Regression model |

> Note: Model files are large and gitignored. Upload them directly to your hosting platform.

