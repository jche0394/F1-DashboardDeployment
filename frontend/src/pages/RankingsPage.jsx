import React, { useState, useEffect } from 'react';
import YearSelector from '../components/rankings/YearSelector';
import fastf1Api from '../services/api';
import DriverRankingsCard from '../components/rankings/DriverRankingsCard';
import CombinedRankingsCard from '../components/rankings/CombinedRankingsCard';
import SyncStatus from '../components/layout/SyncStatus';

export default function RankingsPage() {
  const [driverRankings, setDriverRankings] = useState([]);
  const [combinedRankings, setCombinedRankings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(null);
  const [availableYears, setAvailableYears] = useState([]);
  const [showAllYears, setShowAllYears] = useState(false);

  // Fetch available years on component mount
  useEffect(() => {
    const fetchAvailableYears = async () => {
      try {
        const response = await fetch(`${fastf1Api.baseUrl.replace(/\/+$/, '')}/years`);
        const years = await response.json();
        setAvailableYears(years);
        // Set the latest year as default
        if (years.length > 0) {
          setSelectedYear(years[0]);
        }
      } catch (err) {
        console.error('Error fetching available years:', err);
      }
    };

    fetchAvailableYears();
  }, []);

  // Fetch rankings when selectedYear changes
  useEffect(() => {
    const fetchRankings = async () => {
      if (!selectedYear) return; // Don't fetch if no year is selected
      
      try {
        setLoading(true);
        
        // Build URL with year parameter
        const yearParam = `?season=${selectedYear}`;
        
        // Fetch driver Elo rankings
        const baseUrl = fastf1Api.baseUrl.replace(/\/+$/, '');
        const driverResponse = await fetch(`${baseUrl}/rankings/drivers/elo${yearParam}`);
        const driverData = await driverResponse.json();
        setDriverRankings(driverData.slice(0, 20)); // Top 20 drivers
        
        // Fetch combined rankings
        const combinedResponse = await fetch(`${baseUrl}/rankings/combined${yearParam}`);
        const combinedData = await combinedResponse.json();
        setCombinedRankings(combinedData.slice(0, 20)); // Top 20 combined
        
        setError(null);
      } catch (err) {
        console.error('Error fetching rankings:', err);
        setError('Failed to load rankings. Please check if the backend server is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchRankings();
  }, [selectedYear]);


  if (loading) {
    return (
      <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 text-white bg-gradient-to-r from-yellow-400 via-orange-500 to-red-600 bg-clip-text text-transparent">
            Driver & Constructor Rankings
          </h1>
          <p className="text-lg text-white/70 max-w-4xl mx-auto">
            Elo-based performance rankings tracking driver skill and team performance throughout the season
          </p>
        </div>
        <div className="text-center text-white/60">Loading rankings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 text-white bg-gradient-to-r from-yellow-400 via-orange-500 to-red-600 bg-clip-text text-transparent">
            Driver & Constructor Rankings
          </h1>
          <p className="text-lg text-white/70 max-w-4xl mx-auto">
            Elo-based performance rankings tracking driver skill and team performance throughout the season
          </p>
        </div>
        <div className="text-center p-6 bg-red-500/10 rounded-xl border border-red-500/20">
          <div className="text-red-400 text-lg font-semibold mb-2">Error Loading Rankings</div>
          <div className="text-red-300">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 text-white bg-gradient-to-r from-yellow-400 via-orange-500 to-red-600 bg-clip-text text-transparent">
          Driver & Constructor Rankings
        </h1>
        <p className="text-lg text-white/70 max-w-4xl mx-auto">
          Elo-based performance rankings tracking driver skill and team performance throughout the season
        </p>
      </div>

      {/* Year Selector */}
      <YearSelector
        selectedYear={selectedYear}
        setSelectedYear={setSelectedYear}
        availableYears={availableYears}
        showAllYears={showAllYears}
        setShowAllYears={setShowAllYears}
        loading={loading}
      />

      {/* Summary Stats */}
      {driverRankings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 p-6 rounded-xl border border-yellow-500/20">
            <div className="text-yellow-300 text-sm font-medium mb-2">Top Driver</div>
            <div className="text-white text-xl font-bold">{`${driverRankings[0]?.first_name} ${driverRankings[0]?.last_name}`}</div>
            <div className="text-yellow-300/60 text-xs mt-1">{Math.round(driverRankings[0]?.elo)} Elo</div>
          </div>
          <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 p-6 rounded-xl border border-blue-500/20">
            <div className="text-blue-300 text-sm font-medium mb-2">Total Drivers</div>
            <div className="text-white text-3xl font-bold">{driverRankings.length}</div>
          </div>
          <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 p-6 rounded-xl border border-purple-500/20">
            <div className="text-purple-300 text-sm font-medium mb-2">Avg Elo Rating</div>
            <div className="text-white text-3xl font-bold">
              {Math.round(driverRankings.reduce((sum, d) => sum + d.elo, 0) / driverRankings.length)}
            </div>
          </div>
          <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 p-6 rounded-xl border border-green-500/20">
            <div className="text-green-300 text-sm font-medium mb-2">Season</div>
            <div className="text-white text-3xl font-bold">{selectedYear}</div>
          </div>
        </div>
      )}

      {/* Main grid layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        
        {/* Driver Rankings */}
        <DriverRankingsCard 
          driverRankings={driverRankings}
          selectedYear={selectedYear}
        />

        {/* Combined Driver-Constructor Rankings */}
        <CombinedRankingsCard 
          combinedRankings={combinedRankings}
          selectedYear={selectedYear}
        />
        
      </div>

      {/* Methodology Info */}
      <div className="mt-8 text-sm text-white/60 p-6 bg-gradient-to-r from-black/20 to-black/10 rounded-xl border border-white/10">
        <div className="space-y-3">
          <div className="font-semibold text-white text-lg mb-4">📊 Elo Rating System:</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span><strong>Driver Elo:</strong> Individual driver skill rating based on race results and head-to-head performance</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span><strong>Combined Elo:</strong> Blends driver skill with constructor performance using weighted k-factor</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>Higher ratings indicate consistently better performance throughout the season</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">•</span>
                <span>Rankings update after each race based on finishing positions and competition strength</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Sync Info */}
      <div className="mt-6">
        <SyncStatus />
      </div>
    </div>
  );
}