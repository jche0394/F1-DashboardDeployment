# F1 Dashboard - Deployment Guide

## Overview

This guide covers deploying the F1 Dashboard to Render. The application has been consolidated into a single Flask backend (`app/main.py`) that combines all functionality:
- Ergast API endpoints
- Database-backed ELO rankings
- Race predictions with tire degradation analysis

## Backend Deployment (Render)

### Prerequisites
- Render account (free tier works fine)
- GitHub repository connected to Render

### Deployment Steps

1. **Create a New Web Service on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the Service**
   - **Name**: `f1-dashboard-backend` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app`
   - **Instance Type**: Free tier is sufficient for testing

3. **Environment Variables** (Optional)
   - `PORT`: Automatically set by Render (default: 5000)
   - No other environment variables are required

4. **Advanced Settings**
   - **Auto-Deploy**: Yes (recommended)
   - **Health Check Path**: `/api/health`
   - **Region**: Choose closest to your users

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (first deploy may take 5-10 minutes)

### Verifying Backend Deployment

Once deployed, test these endpoints (replace `YOUR_APP_URL` with your Render URL):

```bash
# Health check
curl https://YOUR_APP_URL.onrender.com/api/health

# Driver standings
curl https://YOUR_APP_URL.onrender.com/api/driver-standings?year=2024

# Race prediction
curl https://YOUR_APP_URL.onrender.com/api/race_predict?year=2025&gp_name=Monaco
```

## Frontend Deployment

### Option 1: Vercel (Recommended for React)

1. **Connect to Vercel**
   - Go to https://vercel.com
   - Import your GitHub repository
   - Select the `frontend` directory as the root

2. **Configure Build Settings**
   - **Framework Preset**: Create React App
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Install Command**: `npm install`

3. **Environment Variables**
   - Add: `REACT_APP_API_URL` = `https://YOUR_APP_URL.onrender.com/api`
   - Make sure to replace YOUR_APP_URL with your actual Render backend URL

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete

### Option 2: Render Static Site

1. **Create a New Static Site**
   - Go to Render dashboard
   - Click "New +" → "Static Site"
   - Connect your repository

2. **Configure**
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/build`

3. **Environment Variables**
   - `REACT_APP_API_URL`: Your backend URL with `/api` suffix

4. **Deploy**
   - Click "Create Static Site"

## Local Development Setup

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask server
cd app
python main.py
```

Server will start on `http://localhost:5000`

### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Create .env file (optional, for custom API URL)
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env

# Start development server
npm start
```

Frontend will start on `http://localhost:3000`

## Architecture Changes

### What Was Combined

The following files have been consolidated into `app/main.py`:

1. **Original `main.py`**
   - Ergast API endpoints (driver-standings, constructor-standings, etc.)
   - Basic health check

2. **`api_retrival/apis.py`** (consolidated into main.py)
   - Database connection and queries
   - ELO rankings endpoints
   - Driver/constructor comparisons
   - Historical data endpoints

3. **`api_retrival/predict_race.py`** (consolidated into main.py)
   - Race prediction algorithm
   - Tire degradation analysis
   - Qualifying data processing

### File Structure

```
F1-Dashboard/
├── app/
│   ├── main.py                    # ✅ CONSOLIDATED BACKEND
│   └── api_retrival/
│       ├── database/
│       │   └── f1_data.db         # Required for ELO data
│       ├── update.py              # Used by GitHub Actions
│       └── ...
├── frontend/
│   └── src/
│       └── services/
│           └── api.js             # ✅ Updated to use unified API
├── requirements.txt               # ✅ Updated (removed FastAPI/uvicorn)
├── Procfile                       # ✅ Updated to use app.main:app
└── README.md                      # ✅ Updated with all endpoints
```

### API Changes

**No Breaking Changes** - All endpoints remain the same, but:
- All endpoints now served from the same Flask app
- Race predictions now at `/api/race_predict` (same path, different server)
- Error responses now use Flask format (`{"error": "..."}`) instead of FastAPI format

## Troubleshooting

### Backend Issues

**Problem**: App crashes on startup
- **Check**: Are all dependencies in `requirements.txt`?
- **Check**: Does the database file exist at `app/api_retrival/database/f1_data.db`?
- **Solution**: Check Render logs for specific error messages

**Problem**: Database errors
- **Check**: Is `f1_data.db` included in the repository?
- **Solution**: Make sure the database file is not in `.gitignore`

**Problem**: FastF1 cache errors
- **Check**: Does Render have enough disk space?
- **Solution**: Cache is created automatically; may slow down first requests

### Frontend Issues

**Problem**: API calls fail with CORS errors
- **Check**: Is CORS enabled in `main.py`? (It should be)
- **Check**: Is `REACT_APP_API_URL` set correctly?
- **Solution**: Verify environment variable includes `/api` suffix

**Problem**: Race predictions return 404
- **Check**: Is the race name spelled correctly?
- **Check**: Does qualifying data exist for that race?
- **Solution**: Check backend logs for specific error

**Problem**: Environment variable not working
- **Check**: Did you rebuild after adding the variable?
- **Solution**: On Vercel/Render, redeploy after changing env vars

## Performance Optimization

### Backend
- FastF1 cache is automatically maintained in `f1_cache/`
- First request to each endpoint may be slow (populating cache)
- Subsequent requests are much faster

### Frontend
- API responses are cached for 5 minutes
- Clear cache with `fastf1Api.clearCache()` in browser console if needed

## Monitoring

### Health Checks
- **Endpoint**: `/api/health`
- **Expected Response**: 
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-10-22T...",
    "message": "F1 Dashboard API - Combined Backend",
    "endpoints": { ... }
  }
  ```

### Render Metrics
- Monitor response times in Render dashboard
- Check logs for errors
- Set up email alerts for downtime

## Cost Estimates

### Free Tier (Render)
- Backend: Free tier includes 750 hours/month
- Note: Free tier spins down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds

### Paid Tier (Render Starter - $7/month)
- Always-on service (no spin-down)
- Faster response times
- More resources

## Next Steps

1. ✅ Backend deployed to Render
2. ✅ Frontend configured with API URL
3. ✅ Test all endpoints
4. 🔄 Set up custom domain (optional)
5. 🔄 Configure CDN (optional)
6. 🔄 Set up monitoring alerts

## Support

For issues:
1. Check Render logs for backend errors
2. Check browser console for frontend errors
3. Test endpoints with `curl` to isolate issues
4. Review this deployment guide

## API Endpoint Reference

Quick reference of all available endpoints:

```
GET  /api/health                                    - Health check
GET  /api/driver-standings                          - Current standings
GET  /api/constructor-standings                     - Constructor standings
GET  /api/season-schedule                           - Race calendar
GET  /api/race-results                              - Race results
GET  /api/qualifying-results                        - Qualifying results
GET  /api/drivers                                   - All drivers
GET  /api/constructors                              - All constructors
GET  /api/circuits                                  - All circuits
GET  /api/rankings/drivers/elo                      - Driver ELO rankings
GET  /api/rankings/constructors/elo                 - Constructor ELO
GET  /api/rankings/combined                         - Combined ELO
GET  /api/rankings/drivers/elo/history/:id          - Driver ELO history
GET  /api/drivers/compare/:id1/:id2                 - Compare drivers
GET  /api/constructors/compare/:id1/:id2            - Compare constructors
GET  /api/race_predict?year=2025&gp_name=Monaco    - Predict race results
```

---

**Last Updated**: October 2025
**Backend Version**: Combined Flask API (main.py)
**Frontend Version**: React with unified API client

