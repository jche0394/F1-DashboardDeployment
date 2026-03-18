import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardCard from '../components/layout/DashboardCard';
import GPSSelector from '../components/shared/GPSSelector';
import SyncStatus from '../components/layout/SyncStatus';

export default function PredictionsPage() {
  const navigate = useNavigate();
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedRace, setSelectedRace] = useState('');
  const [availableRaces, setAvailableRaces] = useState([]);
  const [checkingRaces, setCheckingRaces] = useState(true);
  const [showErrorPopup, setShowErrorPopup] = useState(false);

  // === 🧩 Fetch races that actually have qualifying data in DB ===
  const fetchRaceCalendar = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:5001/api/available_races/2025`);
      if (!response.ok) throw new Error('Failed to fetch available races');
      const data = await response.json();

      // Map names to simplified GP format for frontend consistency
      const calendar = data.map((raceName) => {
        let predictionName = raceName;
        if (raceName.includes('Australian')) predictionName = 'Australia';
        else if (raceName.includes('Chinese')) predictionName = 'China';
        else if (raceName.includes('Japanese')) predictionName = 'Japan';
        else if (raceName.includes('Bahrain')) predictionName = 'Bahrain';
        else if (raceName.includes('Saudi Arabian')) predictionName = 'Saudi Arabia';
        else if (raceName.includes('Miami')) predictionName = 'Miami';
        else if (raceName.includes('Emilia Romagna')) predictionName = 'Emilia Romagna';
        else if (raceName.includes('Monaco')) predictionName = 'Monaco';
        else if (raceName.includes('Spanish')) predictionName = 'Spain';
        else if (raceName.includes('Canadian')) predictionName = 'Canada';
        else if (raceName.includes('Austrian')) predictionName = 'Austria';
        else if (raceName.includes('British')) predictionName = 'Great Britain';
        else if (raceName.includes('Belgian')) predictionName = 'Belgium';
        else if (raceName.includes('Hungarian')) predictionName = 'Hungary';
        else if (raceName.includes('Dutch')) predictionName = 'Netherlands';
        else if (raceName.includes('Italian')) predictionName = 'Italy';
        else if (raceName.includes('Azerbaijan')) predictionName = 'Azerbaijan';
        else if (raceName.includes('Singapore')) predictionName = 'Singapore';
        else if (raceName.includes('United States') && !raceName.includes('Miami')) predictionName = 'United States';
        else if (raceName.includes('Mexico City')) predictionName = 'Mexico';
        else if (raceName.includes('São Paulo')) predictionName = 'Brazil';
        else if (raceName.includes('Las Vegas')) predictionName = 'United States';
        else if (raceName.includes('Qatar')) predictionName = 'Qatar';
        else if (raceName.includes('Abu Dhabi')) predictionName = 'Abu Dhabi';
        return { name: predictionName, raceName };
      });

      return calendar;
    } catch (err) {
      console.error('Error fetching race calendar:', err);
      return [];
    }
  };

  // === 🧩 Fetch predictions from backend ===
  const fetchPredictions = async () => {
    if (!selectedRace) return;
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `http://127.0.0.1:5001/api/race_predict?year=2025&gp_name=${encodeURIComponent(selectedRace)}`
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setPredictions(data);
    } catch (err) {
      console.error('Error fetching predictions:', err);
      setError(err.message);
      setShowErrorPopup(true);
    } finally {
      setLoading(false);
    }
  };

  // === 🧩 Load available races once ===
  useEffect(() => {
    const loadRaceCalendar = async () => {
      const calendar = await fetchRaceCalendar();
      const available = calendar.map(r => r.name);
      setAvailableRaces(available);
      setCheckingRaces(false);

      if (available.length > 0) setSelectedRace(available[0]);
    };
    loadRaceCalendar();
  }, []);

  // === 🧩 Fetch predictions when selection changes ===
  useEffect(() => {
    if (availableRaces.length > 0 && selectedRace) {
      fetchPredictions();
    }
  }, [selectedRace, availableRaces]);

  // === UI states ===
  if (checkingRaces) {
    return (
      <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto text-center">
        <h1 className="text-4xl font-bold mb-4 text-white bg-gradient-to-r from-blue-400 via-purple-500 to-red-500 bg-clip-text text-transparent">
          Race Predictions
        </h1>
        <p className="text-white/70">Loading available races...</p>
      </div>
    );
  }

  if (availableRaces.length === 0) {
    return (
      <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto text-center">
        <h1 className="text-4xl font-bold mb-4 text-white bg-gradient-to-r from-blue-400 via-purple-500 to-red-500 bg-clip-text text-transparent">
          Race Predictions
        </h1>
        <p className="text-lg text-white/70">No 2025 races with qualifying data yet.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto text-center">
        <h1 className="text-4xl font-bold mb-4 text-white bg-gradient-to-r from-blue-400 via-purple-500 to-red-500 bg-clip-text text-transparent">
          Race Predictions
        </h1>
        <p className="text-white/70">Loading race predictions...</p>
      </div>
    );
  }

  const ErrorPopup = () =>
    showErrorPopup && (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 max-w-md mx-4 border border-gray-600 text-center">
          <div className="text-red-400 text-lg font-semibold mb-4">Prediction API Error</div>
          <div className="text-gray-300 mb-6">{error}</div>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => {
                setShowErrorPopup(false);
                setError(null);
              }}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );

  return (
    <>
      <ErrorPopup />
      <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-white bg-gradient-to-r from-blue-400 via-purple-500 to-red-500 bg-clip-text text-transparent">
            Race Predictions
          </h1>
          <p className="text-lg text-white/70">
            Machine learning race predictions based on qualifying results and tire degradation analysis
          </p>
        </div>

        {/* Race selector */}
        <div className="mb-8">
          <GPSSelector
            selectedGP={selectedRace}
            setSelectedGP={setSelectedRace}
            availableGPs={availableRaces}
            loading={loading}
          />
        </div>

        {/* Prediction table */}
        {predictions && (
          <DashboardCard title={`2025 ${selectedRace} GP - Race Predictions`}>
            <div className="overflow-x-auto max-h-[32rem] overflow-y-auto custom-scrollbar">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-white/80 border-b border-white/10">
                    <th className="pb-3 font-semibold">Predicted</th>
                    <th className="pb-3 font-semibold">Driver</th>
                    <th className="pb-3 font-semibold">Team</th>
                    <th className="pb-3 font-semibold">Qualifying</th>
                    <th className="pb-3 font-semibold">Q Time</th>
                    <th className="pb-3 font-semibold">Tire Performance</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.predictions.slice(0, 20).map((p) => {
                    const positionChange = p.predicted_race_position - p.qualifying_position;
                    const teamName = p.constructor_name || 'Unknown';
                    return (
                      <tr key={p.position} className="border-t border-white/10 hover:bg-white/5 transition-colors">
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2">
                            <span className="text-white font-bold text-lg">{p.predicted_race_position}</span>
                            {positionChange !== 0 && (
                              <span
                                className={`text-xs px-2 py-1 rounded-full font-medium ${
                                  positionChange < 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                                }`}
                              >
                                {positionChange < 0 ? `+${Math.abs(positionChange)}` : `-${positionChange}`}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 pr-4 text-white font-medium">{p.driver}</td>
                        <td className="py-3 pr-4 text-white/80 text-sm">{teamName}</td>
                        <td className="py-3 pr-4 text-white/80 font-medium">P{p.qualifying_position}</td>
                        <td className="py-3 pr-4 text-white/80 text-sm">
                          {p.qualifying_time ? `${p.qualifying_time.toFixed(3)}s` : 'N/A'}
                        </td>
                        <td className="py-3 text-white/80">
                          {p.tire_deg_rate !== null && p.tire_deg_rate !== undefined ? (
                            <div className="flex flex-col gap-2">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    p.tire_deg_rate < 0
                                      ? 'bg-green-500/20 text-green-400'
                                      : p.tire_deg_rate < 0.5
                                      ? 'bg-yellow-500/20 text-yellow-400'
                                      : 'bg-red-500/20 text-red-400'
                                  }`}
                                >
                                  {p.tire_deg_rate < 0
                                    ? 'Excellent Tire Life'
                                    : p.tire_deg_rate < 0.5
                                    ? 'Good Tire Life'
                                    : 'Poor Tire Life'}
                                </span>
                                <span
                                  className={`px-2 py-1 rounded-full text-xs font-medium ${
                                    p.prediction_method === 'qualifying_and_tire_deg'
                                      ? 'bg-blue-500/20 text-blue-400'
                                      : 'bg-orange-500/20 text-orange-400'
                                  }`}
                                >
                                  {p.prediction_method === 'qualifying_and_tire_deg'
                                    ? 'High Confidence'
                                    : 'Medium Confidence'}
                                </span>
                              </div>
                              <div className="text-xs text-white/60">
                                Tire degradation: {p.tire_deg_rate.toFixed(3)}s/lap
                              </div>
                            </div>
                          ) : (
                            <div className="flex flex-col gap-2">
                              <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-500/20 text-gray-400">
                                Qualifying Only
                              </span>
                              <span className="text-xs text-white/40">No tire data available</span>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </DashboardCard>
        )}

        <div className="mt-6">
          <SyncStatus />
        </div>
      </div>
    </>
  );
}
