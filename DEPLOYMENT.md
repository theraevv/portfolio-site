# Deployment Guide

## Architecture

This project has two parts:
1. **Frontend** (HTML/CSS/JS) → Deploy to **Cloudflare Pages**
2. **Backend** (Flask + ML models) → Deploy to **Render.com** (free tier)

> **Note:** Cloudflare Pages only hosts static sites. The Python Flask backend with ML models must run on a separate Python-compatible host.

---

## Step 1: Prepare Models for Deployment

Before deploying, copy ALL model files into a `models/` folder inside this project:

```
portfolio-site/
├── models/
│   ├── crop_model.pkl          (from C:\Projects\Websites\Crop Reco\Models\random_forest_model.pkl)
│   ├── diabetes_model.pkl      (from C:\Projects\Websites\Earlt Stage of diabetes\model\best_rf.pkl)
│   ├── mental_burn_model.pkl   (from C:\Projects\Websites\Mental Health\Model\random_forest_model_burn.pkl)
│   ├── mental_dep_model.pkl    (from C:\Projects\Websites\Mental Health\Model\random_forest_model_dep.pkl)
│   ├── mental_anx_model.pkl    (from C:\Projects\Websites\Mental Health\Model\random_forest_model_anx.pkl)
│   └── spam_model.pkl          (model.pkl already in project root)
```

The `app.py` already uses relative paths pointing to the `models/` directory.

---

## Step 2: Push to GitHub

```bash
# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Create GitHub repo (via web or gh CLI), then push
git remote add origin https://github.com/YOUR_USERNAME/portfolio-site.git
git branch -M main
git push -u origin main
```

> **Tip:** Model files (`.pkl`) are large. Either:
> - Use [Git LFS](https://git-lfs.github.com/) to track them, OR
> - Upload them directly to your hosting platform (Render) instead of GitHub.

---

## Step 3: Deploy Frontend to Cloudflare Pages

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Pages**
2. Click **Create a project** → **Connect to Git**
3. Select your `portfolio-site` GitHub repository
4. Configure build:
   - **Framework preset:** None
   - **Build command:** (leave empty)
   - **Build output directory:** `/`
5. Click **Save and Deploy**

Your static site will be live at `https://portfolio-site.pages.dev`

---

## Step 4: Deploy Backend to Render.com

1. Go to [render.com](https://render.com) and sign up (free)
2. Click **New +** → **Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free
5. Add environment variable if needed: `PYTHON_VERSION=3.9`
6. Click **Create Web Service**

Your API will be live at `https://portfolio-api.onrender.com` (example URL).

> **Note:** Add `gunicorn` to `requirements.txt` before deploying:
> ```
> flask
> gunicorn
> joblib
> scikit-learn
> pandas
> numpy
> ```

---

## Step 5: Update Frontend API URLs

After both are deployed, update the JavaScript `fetch` calls in each project page to use your Render backend URL instead of relative paths:

**Before:**
```javascript
fetch("/api/predict/spam", ...)
```

**After:**
```javascript
fetch("https://your-app.onrender.com/api/predict/spam", ...)
```

Update in:
- `crop-reco.html`
- `diabetes-awareness.html`
- `mental-health-awareness.html`
- `spam-detector.html`

Then commit and push — Cloudflare Pages will auto-redeploy.

---

## Alternative: All-in-One on Render

If you prefer a simpler setup, you can deploy **both frontend and backend** on Render as a single Flask app:

1. Render serves the static files via Flask (`send_from_directory`)
2. The API endpoints work on the same domain
3. No need to update fetch URLs or use Cloudflare Pages

To do this, just deploy the entire repo to Render as a Python Web Service. The app.py already handles static file serving.

---

## Quick Checklist

- [ ] Copy all `.pkl` model files into `models/` folder
- [ ] Add `gunicorn` to `requirements.txt`
- [ ] Commit and push to GitHub
- [ ] Deploy frontend to Cloudflare Pages
- [ ] Deploy backend to Render.com
- [ ] Update fetch URLs in HTML files to point to Render backend
- [ ] Commit, push, and verify


