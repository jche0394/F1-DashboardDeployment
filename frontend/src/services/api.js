// FastF1 API Service for CRA + Vercel

const BASE_URL = (process.env.REACT_APP_API_URL || '').replace(/\/+$/, ''); // strip trailing slashes

function join(base, path) {
  // ensures exactly one slash between base and path
  return `${base}/${String(path).replace(/^\/+/, '')}`;
}

class FastF1ApiService {
  constructor() {
    // Unified API endpoint - all endpoints (including predictions) are now in main.py
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
    // For production: https://f1-dashboard-doj4.onrender.com/api
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000;
  }

  async fetchWithCache(key, fetchFn) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) return cached.data;
    const data = await fetchFn();
    this.cache.set(key, { data, timestamp: Date.now() });
    return data;
  }

  async makeRequest(endpoint, params = {}) {
    const url = new URL(join(this.baseUrl, endpoint));
    Object.entries(params).forEach(([k, v]) => {
      if (v !== null && v !== undefined) url.searchParams.append(k, v);
    });

    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  // Endpoints
  getDriverStandings(year = 'current') {
    return this.fetchWithCache(`driverStandings_${year}`, () =>
      this.makeRequest('/driver-standings', { year })
    );
  }

  getConstructorStandings(year = 'current') {
    return this.fetchWithCache(`constructorStandings_${year}`, () =>
      this.makeRequest('/constructor-standings', { year })
    );
  }

  getSeasonSchedule(year = 'current') {
    return this.fetchWithCache(`schedule_${year}`, () =>
      this.makeRequest('/season-schedule', { year })
    );
  }

  getRaceResults(year = 'current', round = null) {
    return this.fetchWithCache(`raceResults_${year}_${round || 'latest'}`, () =>
      this.makeRequest('/race-results', { year, round })
    );
  }

  getQualifyingResults(year = 'current', round = null) {
    return this.fetchWithCache(`qualifying_${year}_${round || 'latest'}`, () =>
      this.makeRequest('/qualifying-results', { year, round })
    );
  }

  async getPointsHistory() {
    // Use existing endpoints to build points history
    const cacheKey = 'pointsHistory_2025';
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    try {
      // Get 2025 season schedule
      const scheduleData = await this.getSeasonSchedule('2025');
      const races = scheduleData.MRData.RaceTable.Races;
      const today = new Date();
      
      // Find completed races only
      const completedRaces = races.filter(race => new Date(race.date) < today);
      
      if (completedRaces.length === 0) {
        return { year: '2025', pointsHistory: [], totalRaces: 0 };
      }
      
      // Sort by round number
      completedRaces.sort((a, b) => a.round - b.round);
      
      // Initialize points tracking
      const driverPoints = {};
      const pointsHistory = [];
      
      // Process each completed race
      for (const race of completedRaces) {
        try {
          // Get race results for this round
          const resultsData = await this.getRaceResults('2025', race.round);
          const raceResults = resultsData.MRData.RaceTable.Races[0].Results;
          
          // Update cumulative points for each driver
          for (const result of raceResults) {
            const driverName = `${result.Driver.givenName} ${result.Driver.familyName}`;
            const pointsEarned = parseFloat(result.points) || 0;
            
            if (!driverPoints[driverName]) {
              driverPoints[driverName] = 0;
            }
            driverPoints[driverName] += pointsEarned;
          }
          
          // Store snapshot of current standings
          const raceData = {
            round: race.round,
            raceName: race.raceName,
            date: race.date,
            standings: []
          };
          
          // Add current standings for all drivers
          for (const [driver, totalPoints] of Object.entries(driverPoints)) {
            raceData.standings.push({
              driver: driver,
              points: totalPoints
            });
          }
          
          // Sort by points (descending)
          raceData.standings.sort((a, b) => b.points - a.points);
          pointsHistory.push(raceData);
          
        } catch (err) {
          console.error(`Error processing race ${race.round}:`, err);
          continue;
        }
      }
      
      const result = {
        year: '2025',
        pointsHistory: pointsHistory,
        totalRaces: pointsHistory.length
      };
      
      this.cache.set(cacheKey, { data: result, timestamp: Date.now() });
      return result;
      
    } catch (err) {
      console.error('Error building points history:', err);
      throw err;
    }
  }

  getConstructors(year = 'current') {
    return this.fetchWithCache(`constructors_${year}`, () =>
      this.makeRequest('/constructors', { year })
    );
  }

  getDrivers(year = 'current') {
    return this.fetchWithCache(`drivers_${year}`, () =>
      this.makeRequest('/drivers', { year })
    );
  }

  getCircuits(year = 'current') {
    return this.fetchWithCache(`circuits_${year}`, () =>
      this.makeRequest('/circuits', { year })
    );
  }

  async healthCheck() {
    const res = await fetch(join(this.baseUrl, '/health'));
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  }

  clearCache() { this.cache.clear(); }
  getCacheStatus() {
    const now = Date.now();
    return [...this.cache.entries()].map(([key, v]) => ({
      key, age: now - v.timestamp, isValid: now - v.timestamp < this.cacheTimeout
    }));
  }

  async isAvailable() {
    try { await this.healthCheck(); return true; } catch { return false; }
  }

  // Race Prediction API - Now unified with main API
  async getRacePrediction(year, gpName) {
    return this.fetchWithCache(`racePrediction_${year}_${gpName}`, () => {
      const url = new URL(join(this.baseUrl, '/race_predict'));
      url.searchParams.append('year', year);
      url.searchParams.append('gp_name', gpName);
      
      return fetch(url.toString()).then(async res => {
        if (!res.ok) {
          const errorData = await res.json();
          const error = new Error(errorData.error || errorData.detail || `HTTP ${res.status}`);
          error.response = {
            status: res.status,
            data: errorData
          };
          throw error;
        }
        return res.json();
      });
    });
  }
}

export default new FastF1ApiService();
