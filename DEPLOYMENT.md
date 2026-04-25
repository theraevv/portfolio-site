# Vercel Deployment Guide

## Option 1: Vercel + Serverless Functions (Recommended)

Vercel supports Python serverless functions, allowing you to run your Flask backend as API routes.

### Project Structure for Vercel

```
portfolio-site/
├── api/
│   └── index.py          # Main API handler
├── static/               # HTML, CSS, JS files
│   ├── index.html
│   ├── styles.css
│   └── ...
├── models/               # .pkl model files
│   ├── spam_model.pkl
│   └── ...
├── requirements.txt
└── vercel.json
```

### Steps

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Restructure for Vercel**
   - Move all HTML/CSS/JS to a `static/` folder
   - Create `api/index.py` as the entry point
   - Create `vercel.json` config

3. **Deploy**
   ```bash
   vercel
   ```

## Option 2: Static Frontend Only (No ML Backend)

If you only need the frontend without ML predictions:

1. Connect your GitHub repo to [vercel.com](https://vercel.com)
2. Framework preset: **Other**
3. Build command: *(empty)*
4. Output directory: `/` (root)
5. Deploy

The frontend will work but API calls will fail.

## Option 3: Vercel Frontend + Render Backend

1. **Frontend on Vercel:**
   - Deploy static files to Vercel
   - Update `config.js` with your Render backend URL:
     ```javascript
     const API_BASE = "https://your-app.onrender.com";
     ```

2. **Backend on Render:**
   - Deploy Flask app to [render.com](https://render.com)
   - Upload model files to `models/` directory

## Current Setup

This project is currently configured for **Option 3**:
- `config.js` has `API_BASE = ""` (same-origin)
- `app.py` has CORS enabled for cross-origin requests
- Update `config.js` when deploying frontend and backend separately
