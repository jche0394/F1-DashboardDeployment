# Fix Render Backend Deployment (Predictions Not Working)

If `/api/available_races` and `/api/race_predict` return 404, or you see "API returned HTML instead of JSON", the backend is running an old build. Follow these steps to fix it.

## 1. Verify GitHub Has Latest Code

Ensure the latest code is pushed:
```bash
git add -A
git commit -m "Enable predictions on Render"
git push origin main
```

## 2. Check Render Dashboard

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Find your **backend** Web Service (the one that serves the API, not the frontend static site)
3. Confirm the service name/URL matches where your frontend sends API requests (e.g. `f1-dashboard-vf4u.onrender.com`)

## 3. Critical Settings (Backend Web Service)

| Setting | Required Value |
|---------|----------------|
| **Repository** | `jche0394/F1-DashboardDeployment` (or your fork) |
| **Branch** | `main` |
| **Root Directory** | Leave **empty** (repo root) |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app.main:app` |
| **Auto-Deploy** | Yes |

**Important:** If "Root Directory" is set to `frontend` or anything else, the backend will fail or run wrong code. For the Flask backend, it must be empty so Render uses the repo root (`app/`, `requirements.txt`, `Procfile`).

## 4. Force Fresh Deploy

1. Open your backend service in Render
2. Click **Manual Deploy** (top right)
3. Select **Clear build cache & deploy**
4. Wait for the build to finish (check Logs for errors)

## 5. Verify New Build Is Live

After deploy, open:
```
https://YOUR-BACKEND-URL.onrender.com/api/health
```

You should see:
- `"build": "2026-03-predictions"`
- `"predictions": ["/api/available_races/<year>", "/api/race_predict"]`

If you still see `"note": "Race predictions not available on Render"` or no `build` field, the old code is still running. In that case:
- Double-check **Repository** and **Branch** in Render
- Ensure you're editing the correct service (backend, not frontend)
- Try disconnecting and reconnecting the GitHub repo

## 6. Recreate Backend (Last Resort)

If the above doesn't work, create a new Web Service:

1. **New +** → **Web Service**
2. Connect `jche0394/F1-DashboardDeployment` (or your repo)
3. **Root Directory**: leave empty
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `gunicorn app.main:app`
6. Create the service
7. Copy the new URL and update `REACT_APP_API_URL` in your frontend's environment variables (Vercel, etc.)
