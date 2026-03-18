// FastF1 API Service for CRA + Vercel

function join(base, path) {
  // ensures exactly one slash between base and path
  return `${base}/${String(path).replace(/^\/+/, '')}`;
}

async function parseJsonOrThrow(res, context = '') {
  const text = await res.text();
  return parseJsonFromText(text, context, res.status);
}

function parseJsonFromText(text, context = '', status = 0) {
  if (!text) return null;
  if (text.trimStart().startsWith('<')) {
    throw new Error(
      context
        ? `${context}: Server returned HTML instead of JSON (check API URL; got ${status})`
        : `Server returned HTML instead of JSON (check REACT_APP_API_URL; got ${status})`
    );
  }
  try {
    return JSON.parse(text);
  } catch (e) {
    throw new Error(context ? `${context}: Invalid JSON` : 'Invalid JSON response');
  }
}

class FastF1ApiService {
  constructor() {
    // Unified API endpoint - all endpoints (including predictions) are now in main.py
    this.baseUrl = process.env.REACT_APP_API_URL || 'https://f1-dashboard-vf4u.onrender.com/api';
    // Set REACT_APP_API_URL=http://localhost:5000/api for local backend development
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
    return parseJsonOrThrow(res);
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
    const year = new Date().getFullYear();
    const cacheKey = `pointsHistory_${year}`;
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    try {
      // Get current season schedule
      const scheduleData = await this.getSeasonSchedule(String(year));
      const races = scheduleData.MRData.RaceTable.Races;
      const today = new Date();
      
      // Find completed races only
      const completedRaces = races.filter(race => new Date(race.date) < today);
      
      if (completedRaces.length === 0) {
        return { year: String(year), pointsHistory: [], totalRaces: 0 };
      }
      
      // Sort by round number
      completedRaces.sort((a, b) => a.round - b.round);
      
      // Fetch all race results in parallel (much faster than sequential)
      const resultsWithRaces = await Promise.all(
        completedRaces.map(async (race) => {
          try {
            const resultsData = await this.getRaceResults(String(year), race.round);
            return { race, resultsData };
          } catch (err) {
            console.error(`Error fetching race ${race.round}:`, err);
            return { race, resultsData: null };
          }
        })
      );

      // Build cumulative points history in round order
      const driverPoints = {};
      const pointsHistory = [];

      for (const { race, resultsData } of resultsWithRaces) {
        if (!resultsData?.MRData?.RaceTable?.Races?.[0]?.Results) continue;

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

        for (const [driver, totalPoints] of Object.entries(driverPoints)) {
          raceData.standings.push({ driver, points: totalPoints });
        }

        raceData.standings.sort((a, b) => b.points - a.points);
        pointsHistory.push(raceData);
      }
      
      const result = {
        year: String(year),
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
    return parseJsonOrThrow(res, 'health');
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

  // Available races for a given year (multi-year support)
  // Falls back to season-schedule if available_races returns 404 (e.g. older Render deployment)
  async getAvailableRaces(year) {
    const url = join(this.baseUrl, `available_races/${year}`);
    const res = await fetch(`${url}?_t=${Date.now()}`, { cache: 'no-store' });
    if (res.ok) return parseJsonOrThrow(res, 'available_races');

    if (res.status === 404) {
      // Fallback: use season-schedule (works on Render when available_races is not deployed)
      try {
        const scheduleData = await this.getSeasonSchedule(String(year));
        const races = scheduleData?.MRData?.RaceTable?.Races || [];
        return races.map((r) => r.raceName).filter(Boolean);
      } catch (fallbackErr) {
        console.warn('available_races 404 and season-schedule fallback failed:', fallbackErr);
      }
    }

    const text = await res.text();
    if (text.trimStart().startsWith('<')) {
      throw new Error(
        'API returned HTML instead of JSON. Check REACT_APP_API_URL points to the backend (e.g. https://f1-dashboard-vf4u.onrender.com/api).'
      );
    }
    let err = {};
    try {
      err = JSON.parse(text);
    } catch {}
    throw new Error(err.error || `HTTP ${res.status}`);
  }

  // Race Prediction API - Now unified with main API
  async getRacePrediction(year, gpName) {
    return this.fetchWithCache(`racePrediction_${year}_${gpName}`, () => {
      const url = new URL(join(this.baseUrl, '/race_predict'));
      url.searchParams.append('year', year);
      url.searchParams.append('gp_name', gpName);
      
      return fetch(url.toString()).then(async res => {
        const text = await res.text();
        if (!res.ok) {
          if (text.trimStart().startsWith('<')) {
            const msg =
              res.status === 404
                ? 'Prediction API returned 404 (route may not be deployed). Redeploy the backend on Render with the latest code, or run the backend locally (localhost:8000) and set REACT_APP_API_URL=http://localhost:8000/api.'
                : `API returned HTML instead of JSON (HTTP ${res.status}). Check REACT_APP_API_URL points to the backend.`;
            throw new Error(msg);
          }
          let errorData = {};
          try {
            errorData = JSON.parse(text);
          } catch {}
          const error = new Error(errorData.error || errorData.detail || `HTTP ${res.status}`);
          error.response = { status: res.status, data: errorData };
          throw error;
        }
        return parseJsonFromText(text, 'race_predict');
      });
    });
  }
}

const fastF1Api = new FastF1ApiService();
export default fastF1Api;
