# F1 Dashboard - Quick Start Guide

## 🎉 Consolidation Complete!

Your F1 Dashboard backend has been successfully consolidated into a single Flask application ready for Render deployment.

## What Changed?

✅ Combined `predict_race.py` + `apis.py` → `main.py`  
✅ Updated `Procfile` to point to unified app  
✅ Removed unnecessary FastAPI dependencies  
✅ Updated frontend to use unified API endpoint  
✅ Created comprehensive documentation  

## Quick Deploy to Render

### Step 1: Push to GitHub
```bash
cd /Users/josh/Developer/F1-Dashboard

# Review changes
git status

# Stage all changes
git add .

# Commit
git commit -m "Consolidate backend: combine predict_race.py and apis.py into main.py for Render deployment"

# Push
git push origin main
```

### Step 2: Deploy on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `f1-dashboard-backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app`
5. Click **"Create Web Service"**
6. Wait for deployment (~5-10 minutes)

### Step 3: Update Frontend

Once backend is deployed, update your frontend environment variable:

```bash
# In your frontend deployment (Vercel/Render/etc.)
REACT_APP_API_URL=https://f1-dashboard-vf4u.onrender.com/api
```

### Step 4: Test

```bash
# Health check
curl https://f1-dashboard-vf4u.onrender.com/api/health

# Test race prediction
curl "https://f1-dashboard-vf4u.onrender.com/api/race_predict?year=2025&gp_name=Monaco"

# Test ELO rankings
curl "https://f1-dashboard-vf4u.onrender.com/api/rankings/drivers/elo?season=2024"
```

## Local Development

### Start Backend
```bash
cd /Users/josh/Developer/F1-Dashboard
pip install -r requirements.txt
cd app
python main.py
```

Backend runs on: `http://localhost:5000`

### Start Frontend
```bash
cd /Users/josh/Developer/F1-Dashboard/frontend
npm install
npm start
```

Frontend runs on: `http://localhost:3000`

## All Available Endpoints

### 🏁 Race Data (Ergast API)
```
GET /api/driver-standings?year=2024
GET /api/constructor-standings?year=2024
GET /api/season-schedule?year=2025
GET /api/race-results?year=2024&round=10
GET /api/qualifying-results?year=2024&round=10
GET /api/circuits?year=2024
```

### 📊 ELO Rankings (Database)
```
GET /api/rankings/drivers/elo?season=2024&race=10
GET /api/rankings/constructors/elo?season=2024
GET /api/rankings/combined?season=2024
GET /api/rankings/drivers/elo/history/1?season=2024
```

### 🔍 Comparisons
```
GET /api/drivers/compare/1/2
GET /api/constructors/compare/1/2
```

### 🔮 Race Predictions
```
GET /api/race_predict?year=2025&gp_name=Monaco
```

Valid race names:
- Bahrain, Saudi Arabia, Australia, Japan, China, Miami
- Emilia Romagna, Monaco, Canada, Spain, Austria, Great Britain
- Hungary, Belgium, Netherlands, Italy, Azerbaijan, Singapore
- United States, Mexico, Brazil, Qatar, Abu Dhabi

### 💾 Database Access
```
GET /api/drivers
GET /api/constructors
GET /api/driver_race/2024
GET /api/constructor_race/2024
GET /api/years
```

## Testing Your Deployment

Visit your Render app URL and test these:

1. **Health Check**: `https://f1-dashboard-vf4u.onrender.com/api/health`
   - Should return `{"status": "healthy", ...}`

2. **Driver Standings**: `https://f1-dashboard-vf4u.onrender.com/api/driver-standings?year=2024`
   - Should return current F1 standings

3. **Race Prediction**: `https://f1-dashboard-vf4u.onrender.com/api/race_predict?year=2025&gp_name=Monaco`
   - Should return predicted race results

## Troubleshooting

### ❌ "Module not found" error
**Solution**: Make sure `requirements.txt` has all dependencies:
```bash
pip install -r requirements.txt
```

### ❌ "Database not found" error
**Solution**: Ensure `app/api_retrival/database/f1_data.db` exists in your repository

### ❌ "CORS error" in frontend
**Solution**: 
1. Check `REACT_APP_API_URL` environment variable
2. Make sure it includes `/api` at the end
3. Redeploy frontend after changing env vars

### ❌ "Port already in use"
**Solution**:
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port
PORT=5001 python main.py
```

### ❌ Render app is slow/timing out
**Cause**: Free tier spins down after 15 minutes of inactivity

**Solutions**:
- First request after spin-down takes 30-60 seconds (normal)
- Upgrade to paid tier for always-on service
- Use a ping service to keep it awake

## File Structure

```
F1-Dashboard/
├── app/
│   ├── main.py                 ⭐ Main API (all endpoints here!)
│   └── api_retrival/
│       ├── database/
│       │   └── f1_data.db     📊 Required for ELO data
│       ├── update.py          📡 Used by GitHub Actions for DB updates
│       ├── get_deg.py         📡 Tire degradation (used by update.py)
│       └── ...
├── frontend/
│   └── src/
│       └── services/
│           └── api.js         ✅ Updated for unified API
├── Procfile                   ✅ Points to app.main:app
├── requirements.txt           ✅ Flask dependencies only
├── README.md                  📖 Full documentation
├── DEPLOYMENT.md              🚀 Detailed deploy guide
├── CHANGES.md                 📋 What changed
└── QUICKSTART.md             ⚡ This file!
```

## Next Steps

1. ✅ **Commit and push changes** to GitHub
2. ✅ **Deploy backend** to Render
3. ✅ **Get backend URL** from Render dashboard
4. ✅ **Update frontend** with backend URL
5. ✅ **Deploy frontend** to Vercel/Render
6. ✅ **Test everything** works
7. 🎉 **Celebrate!**

## Resources

- **Full Documentation**: See `README.md`
- **Deployment Guide**: See `DEPLOYMENT.md`
- **Change Log**: See `CHANGES.md`
- **Render Docs**: https://render.com/docs
- **FastF1 Docs**: https://theoehrly.github.io/Fast-F1/

## Support

If you run into issues:

1. Check Render logs for backend errors
2. Check browser console for frontend errors
3. Test endpoints with `curl` to isolate issues
4. Review `DEPLOYMENT.md` troubleshooting section

## You're Ready! 🏎️💨

Your F1 Dashboard is now ready for deployment with a unified, production-ready backend!

---

**Last Updated**: October 22, 2025

