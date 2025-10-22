# Your F1 Dashboard Deployment

## 🎯 Your URLs

**Backend API**: https://f1-dashboard-vf4u.onrender.com/api  
**Frontend**: (Update this after deploying)

## ✅ Quick Test Commands

Copy and paste these to test your deployment:

### 1. Health Check
```bash
curl https://f1-dashboard-vf4u.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T...",
  "message": "F1 Dashboard API - Combined Backend"
}
```

### 2. Driver Standings (2024)
```bash
curl https://f1-dashboard-vf4u.onrender.com/api/driver-standings?year=2024
```

### 3. ELO Rankings
```bash
curl https://f1-dashboard-vf4u.onrender.com/api/rankings/drivers/elo?season=2024
```

### 4. Race Prediction (Monaco 2025)
```bash
curl "https://f1-dashboard-vf4u.onrender.com/api/race_predict?year=2025&gp_name=Monaco"
```

### 5. Database - All Drivers
```bash
curl https://f1-dashboard-vf4u.onrender.com/api/drivers
```

### 6. Available Years
```bash
curl https://f1-dashboard-vf4u.onrender.com/api/years
```

## 🔧 Frontend Configuration

### For Local Development
Create `frontend/.env`:
```env
REACT_APP_API_URL=http://localhost:5000/api
```

### For Production (Vercel/Render)
Set environment variable:
```env
REACT_APP_API_URL=https://f1-dashboard-vf4u.onrender.com/api
```

**Note**: Your frontend is already configured to use this URL as the default fallback!

## 📊 Deployment Status Checklist

- [ ] Backend deployed to Render
- [ ] Health check endpoint working
- [ ] Database endpoints returning data
- [ ] Race prediction endpoint working
- [ ] Frontend deployed with correct API URL
- [ ] CORS working (no errors in browser console)
- [ ] FastF1 cache building on first requests

## 🚀 Current Setup

### Backend (Render)
- **URL**: https://f1-dashboard-vf4u.onrender.com
- **App**: Unified Flask app (`app/main.py`)
- **Database**: SQLite (f1_data.db) - included in deployment
- **Endpoints**: 40+ endpoints (Ergast + ELO + Predictions)

### What Works
✅ **Ergast API**: Live F1 data (standings, schedules, results)  
✅ **ELO Rankings**: Historical performance data from database  
✅ **Race Predictions**: Tire degradation analysis  
✅ **Comparisons**: Driver and constructor head-to-head  
✅ **Database**: Read-only SQLite with 2.2MB of data  

### First Request Behavior
⚠️ **Note**: First request after deployment/restart may take 30-60 seconds while:
- Render spins up the service (free tier)
- FastF1 cache is built
- Database is loaded into memory

Subsequent requests will be fast!

## 🔍 Debugging

### Check Render Logs
1. Go to https://dashboard.render.com
2. Find your service: f1-dashboard-vf4u
3. Click "Logs" tab
4. Look for errors or startup messages

### Test Specific Endpoints

**If health check fails:**
```bash
# Check if service is up
curl -I https://f1-dashboard-vf4u.onrender.com/api/health
```

**If database endpoints fail:**
```bash
# Check if database is loaded
curl https://f1-dashboard-vf4u.onrender.com/api/years
# Should return: [2024, 2023, 2022, ...]
```

**If predictions fail:**
```bash
# Try a different race
curl "https://f1-dashboard-vf4u.onrender.com/api/race_predict?year=2025&gp_name=Australia"
```

## 📱 Test in Browser

Open these URLs in your browser:

1. **Health Check**:  
   https://f1-dashboard-vf4u.onrender.com/api/health

2. **Driver Standings**:  
   https://f1-dashboard-vf4u.onrender.com/api/driver-standings?year=2024

3. **ELO Rankings**:  
   https://f1-dashboard-vf4u.onrender.com/api/rankings/drivers/elo?season=2024

4. **Race Prediction**:  
   https://f1-dashboard-vf4u.onrender.com/api/race_predict?year=2025&gp_name=Monaco

## 🔄 Updating Your Deployment

### When You Update ELO Data
```bash
# 1. Update database locally
cd app/api_retrival
python update.py

# 2. Commit and push
git add database/f1_data.db
git commit -m "Update ELO ratings"
git push origin main

# 3. Render auto-deploys in ~2-3 minutes
```

### When You Update Code
```bash
# Any push to main triggers automatic redeployment
git add .
git commit -m "Your changes"
git push origin main
```

## 💡 Pro Tips

1. **Bookmark your health check**: https://f1-dashboard-vf4u.onrender.com/api/health
2. **Keep service awake**: Set up a cron job to ping your API every 10 minutes
3. **Monitor logs**: Check Render dashboard regularly for errors
4. **Test after deploy**: Always run quick tests after deployment

## 🎯 Next Actions

1. **Push your latest changes**:
   ```bash
   git push origin main
   ```

2. **Wait for Render to deploy** (~5 minutes)

3. **Test your endpoints** using the commands above

4. **Deploy frontend** with your API URL

5. **Celebrate!** 🎉

---

**Your Backend**: https://f1-dashboard-vf4u.onrender.com/api  
**Last Updated**: October 22, 2025

