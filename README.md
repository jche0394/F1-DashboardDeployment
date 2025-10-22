# F1 Dashboard

A comprehensive Formula 1 dashboard application with real-time data visualization, ELO rankings, and race predictions.

## Architecture

This application consists of:
- **Backend**: Flask API server (`app/main.py`) combining multiple data sources
  - FastF1 live data and Ergast API
  - SQLite database with ELO ratings
  - Race prediction engine with tire degradation analysis
- **Frontend**: React application with modern UI components

## Setup Instructions

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Flask API server:**
   ```bash
   cd app
   python main.py
   ```
   
   The API server will run on `http://localhost:5000`

### Frontend Setup

1. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the React development server:**
   ```bash
   npm start
   ```
   
   The frontend will run on `http://localhost:3000`

## Deployment (Render)

The application is configured to deploy on Render using the included `Procfile`:

```
web: gunicorn app.main:app
```

**Environment Variables:**
- `PORT`: Set automatically by Render (default: 5000)

**Deployment Steps:**
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app.main:app`
5. Deploy!

## API Endpoints

### Health & Info
- `GET /` or `GET /api/health` - Health check and API info

### Ergast API Endpoints (Live F1 Data)
- `GET /api/driver-standings?year=current` - Get driver standings
- `GET /api/constructor-standings?year=current` - Get constructor standings
- `GET /api/season-schedule?year=current` - Get season schedule
- `GET /api/race-results?year=current&round=1` - Get race results
- `GET /api/qualifying-results?year=current&round=1` - Get qualifying results
- `GET /api/circuits?year=current` - Get circuits list

### Database Endpoints (Historical Data & ELO)
- `GET /api/drivers` - Get all drivers from database
- `GET /api/constructors` - Get all constructors from database
- `GET /api/driver_race/<year>` - Get driver race data for a specific year
- `GET /api/constructor_race/<year>` - Get constructor race data for a specific year
- `GET /api/years` - Get all available years in database

### ELO Rankings & History
- `GET /api/rankings/drivers/elo?season=2024&race=5` - Get driver ELO rankings
  - Optional params: `season` (year), `race` (round number)
- `GET /api/rankings/drivers/elo/history/<driver_id>?season=2024` - Get driver ELO history
- `GET /api/rankings/combined?season=2024&race=5` - Get combined driver-constructor ELO
- `GET /api/rankings/constructors/elo?season=2024&race=5` - Get constructor ELO rankings
- `GET /api/elo/drivers/<year>/<round>` - Get driver ELO for specific race
- `GET /api/elo/constructors/<year>/<round>` - Get constructor ELO for specific race
- `GET /api/elo/combined/<year>/<round>` - Get combined ELO for specific race

### Comparison Endpoints
- `GET /api/drivers/compare/<driver1_id>/<driver2_id>` - Compare two drivers
- `GET /api/constructors/compare/<constructor1_id>/<constructor2_id>` - Compare two constructors

### Race Prediction Endpoints
- `GET /api/race_predict?year=2025&gp_name=Monaco` - Predict race results
  - Uses qualifying times + tire degradation analysis
  - Analyzes Sprint Race > FP2 > FP3 for tire deg data
  - Valid race names: Bahrain, Saudi Arabia, Australia, Japan, China, Miami, Emilia Romagna, Monaco, Canada, Spain, Austria, Great Britain, Hungary, Belgium, Netherlands, Italy, Azerbaijan, Singapore, United States, Mexico, Brazil, Qatar, Abu Dhabi

## Features

- **Real-time F1 Data**: Live driver and constructor standings via Ergast API
- **ELO Rating System**: Historical performance tracking with custom ELO algorithm
- **Race Predictions**: Advanced predictions using qualifying + tire degradation analysis
- **Tire Degradation Analysis**: Calculates tire deg from sprint races or practice sessions
- **Driver & Constructor Comparisons**: Head-to-head comparisons with latest stats
- **Interactive Charts**: ELO rating history and performance analytics
- **Responsive Design**: Modern UI that works on all devices

## Data Sources

- **FastF1 Library**: Python library for accessing F1 telemetry and session data
- **Ergast API**: Historical F1 data through fastf1's Ergast integration
- **SQLite Database**: Local database with ELO ratings and historical race data
- **Cache System**: Intelligent caching of FastF1 data for improved performance

## Race Prediction Methodology

The race prediction engine uses a sophisticated approach:

1. **Qualifying Data**: Fetches official qualifying times and positions
2. **Tire Degradation Analysis**: 
   - Priority: Sprint Race > FP2 > FP3
   - Analyzes long runs (7+ laps in practice, 5+ in sprint)
   - Calculates deg rate: (late laps avg - early laps avg) / laps between
3. **Position Adjustment**:
   - Drivers with top 25% tire management: gain 1-3 positions
   - Drivers with bottom 25% tire management: lose 1-3 positions
   - Middle 50%: minimal change
4. **Constraints**: Maximum ±3 positions from qualifying

## Development

### Backend Development
- **Combined Architecture**: Single `app/main.py` file contains all endpoints
- **Flask Framework**: Unified REST API with CORS enabled
- **Database Access**: SQLite connection with helper functions
- **Caching**: FastF1 cache in `f1_cache/` directory
- **Error Handling**: Comprehensive error messages for all endpoints

### Frontend Development
- React components use the API service to communicate with the backend
- Components include fallback data for offline scenarios
- Modern UI with Tailwind CSS styling

### Project Structure
```
F1-Dashboard/
├── app/
│   ├── main.py                 # Combined Flask API (all endpoints)
│   └── api_retrival/
│       ├── database/
│       │   └── f1_data.db     # SQLite database with ELO data
│       └── [other modules]     # Helper scripts for data processing
├── frontend/
│   └── src/                   # React application
├── f1_cache/                  # FastF1 cache directory
├── requirements.txt           # Python dependencies
├── Procfile                   # Render deployment config
└── README.md                  # This file
```

## Troubleshooting

1. **Backend not starting**: Make sure all Python dependencies are installed
2. **Frontend can't connect to API**: Ensure the Flask server is running on port 5000
3. **No data loading**: Check the browser console for API errors
4. **CORS issues**: The backend has CORS enabled for all origins
5. **Database errors**: Ensure `f1_data.db` exists in `app/api_retrival/database/`
6. **FastF1 cache issues**: Delete `f1_cache/` directory and restart
7. **Race prediction errors**: Ensure qualifying data exists for the requested race

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both backend and frontend
5. Submit a pull request

## License

This project uses publicly available F1 data and is intended for educational purposes.
