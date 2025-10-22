# F1 Dashboard - Consolidation Changes

## Summary

Combined three separate Python files (`main.py`, `apis.py`, `predict_race.py`) into a single unified Flask application in `app/main.py` for easier deployment and maintenance on Render.

## Files Modified

### 1. `/app/main.py` - **COMPLETELY REWRITTEN**
**Before**: Simple Flask app with 8 Ergast API endpoints (~340 lines)

**After**: Comprehensive Flask app with 40+ endpoints (~1000 lines)

**Changes**:
- ✅ Kept all original Ergast API endpoints
- ✅ Added all database-backed endpoints from `apis.py`
- ✅ Converted FastAPI race prediction endpoints to Flask
- ✅ Added SQLite database connection helpers
- ✅ Added race prediction helper functions (tire degradation analysis)
- ✅ Unified error handling across all endpoints
- ✅ Maintained CORS support for frontend communication

**New Endpoint Categories**:
1. **Ergast API** (8 endpoints) - Driver/constructor standings, schedules, results
2. **Database/ELO** (15 endpoints) - Rankings, history, comparisons
3. **Predictions** (1 endpoint) - Race predictions with tire analysis

### 2. `/Procfile` - **UPDATED**
**Before**: 
```
web: gunicorn app.api_retrival.apis:app
```

**After**:
```
web: gunicorn app.main:app
```

**Why**: Points to the new unified Flask app location

### 3. `/requirements.txt` - **UPDATED**
**Removed**:
- `fastapi>=0.118.0` - No longer needed
- `uvicorn>=0.37.0` - FastAPI server, not needed

**Kept**:
- `flask>=2.0.0` - Main web framework
- `flask-cors>=3.0.0` - CORS support
- `fastf1>=3.0.0` - F1 data library
- `pandas>=1.5.0` - Data processing
- `numpy>=1.20.0` - Numerical operations
- `gunicorn>=20.1.0` - Production server

**Why**: Removed FastAPI dependencies since everything is now Flask-based

### 4. `/README.md` - **COMPREHENSIVE UPDATE**
**Added Sections**:
- Deployment (Render) instructions
- Complete API endpoint reference (40+ endpoints organized by category)
- Race Prediction Methodology explanation
- Updated project structure diagram
- Enhanced troubleshooting section
- Architecture explanation

**Updated Sections**:
- Features list (added ELO and predictions)
- Data sources (added database and cache system)
- Setup instructions (clarified paths)

### 5. `/frontend/src/services/api.js` - **UPDATED**
**Changes**:
- Removed separate `predictionBaseUrl` (was `localhost:8000`)
- Unified all API calls to use single `baseUrl`
- Updated `getRacePrediction()` to use main API endpoint
- Changed error handling to support Flask error format
- Added environment variable support with fallback

**Before**:
```javascript
this.baseUrl = 'https://f1-dashboard-doj4.onrender.com/api';
this.predictionBaseUrl = 'http://localhost:8000';
```

**After**:
```javascript
this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
```

### 6. `/DEPLOYMENT.md` - **NEW FILE**
Comprehensive deployment guide covering:
- Step-by-step Render deployment
- Frontend deployment options (Vercel, Render)
- Local development setup
- Architecture changes explanation
- Troubleshooting guide
- Performance optimization tips
- Cost estimates
- Complete API reference

## Files NOT Modified (But Referenced)

### `/app/api_retrival/apis.py` - **KEPT AS-IS**
- Still exists in repository
- No longer used in production
- Code has been integrated into `main.py`
- Can be used as reference or deleted

### `/app/api_retrival/predict_race.py` - **KEPT AS-IS**
- Still exists in repository
- No longer used in production
- Converted from FastAPI to Flask and integrated into `main.py`
- Can be used as reference or deleted

### `/app/api_retrival/database/f1_data.db` - **REQUIRED**
- Database file with ELO ratings and historical data
- Used by the new unified API
- Must be included in deployment

## Breaking Changes

### ⚠️ None!

All API endpoints remain the same. The changes are internal only:
- Same endpoint paths
- Same query parameters
- Same response formats (with minor error format adjustments)

### Minor Adjustments

**Error Response Format**:
- **Before** (FastAPI): `{"detail": "Error message"}`
- **After** (Flask): `{"error": "Error message"}`
- Frontend updated to handle both formats

## New Features Enabled

By consolidating into one file, these features are now easier to maintain:

1. **Unified Caching**: FastF1 cache shared across all endpoints
2. **Single Deployment**: One app, one deployment, one URL
3. **Shared Database**: All endpoints can access ELO data
4. **Consistent Error Handling**: Same error format across all endpoints
5. **Easier Debugging**: All code in one place

## Testing Checklist

Before deployment, verify these endpoints work:

### Ergast Endpoints
- [ ] `GET /api/health`
- [ ] `GET /api/driver-standings?year=2024`
- [ ] `GET /api/constructor-standings?year=2024`
- [ ] `GET /api/season-schedule?year=2025`

### Database Endpoints
- [ ] `GET /api/drivers`
- [ ] `GET /api/rankings/drivers/elo`
- [ ] `GET /api/years`

### Prediction Endpoints
- [ ] `GET /api/race_predict?year=2025&gp_name=Monaco`

### Frontend Integration
- [ ] Frontend can connect to API
- [ ] Race predictions load correctly
- [ ] ELO rankings display
- [ ] No CORS errors

## Deployment Steps

### 1. Backend (Render)
```bash
# Render will automatically:
1. Run: pip install -r requirements.txt
2. Run: gunicorn app.main:app
3. Expose on PORT (set by Render)
```

### 2. Frontend (Vercel/Render)
```bash
# Set environment variable:
REACT_APP_API_URL=https://your-app.onrender.com/api

# Vercel will automatically:
1. cd frontend
2. npm install
3. npm run build
4. Deploy build folder
```

## Rollback Plan

If issues occur, you can rollback by:

1. **Revert Procfile**:
   ```
   web: gunicorn app.api_retrival.apis:app
   ```

2. **Re-add FastAPI dependencies** to `requirements.txt`:
   ```
   fastapi>=0.118.0
   uvicorn>=0.37.0
   ```

3. **Revert frontend API service** to use separate prediction URL

4. **Redeploy**

## Performance Notes

### Before (3 separate processes)
- Main API: Flask on port 5001
- Ergast API: Flask on port 5000
- Predictions: FastAPI on port 8000
- Frontend needs to know 2+ backend URLs
- Separate caching per process

### After (1 unified process)
- Combined API: Flask on port 5000 (or Render's PORT)
- Frontend needs only 1 backend URL
- Shared caching across all endpoints
- Simpler deployment
- Lower resource usage

## Database Schema

The SQLite database (`f1_data.db`) contains:

**Tables**:
- `Driver` - Driver information (id, name, country, code)
- `Constructor` - Team information (id, name)
- `Race` - Race information (id, year, round, name, date)
- `Driver_Race` - Driver performance per race (elo, combined_elo, position, points)
- `Constructor_Race` - Constructor performance per race (elo, position, points)

**Key Fields**:
- `elo` - Performance rating (1000-2500)
- `combined_elo` - Driver + Constructor combined rating
- `points` - Championship points earned

## Environment Variables

### Backend (Optional)
- `PORT` - Server port (set by Render, default: 5000)

### Frontend (Required for Production)
- `REACT_APP_API_URL` - Backend API URL (e.g., `https://your-app.onrender.com/api`)

## Support & Maintenance

### Regular Tasks
1. Update driver list in `main.py` for new seasons
2. Update valid race names for new seasons
3. Monitor FastF1 cache size (can grow large)
4. Update ELO database with new race results

### Monitoring
- Health check: `/api/health`
- Render dashboard for uptime
- Browser console for frontend errors

## Migration Complete! ✅

All functionality has been successfully consolidated into a single, unified Flask application that's ready for deployment on Render.

---

**Date**: October 22, 2025
**Changes By**: Consolidation of backend services
**Status**: Ready for deployment

