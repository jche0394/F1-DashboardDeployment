import React, { useState, useEffect } from 'react';
import fastf1Api from '../../services/api';

export default function ComparisonSummaryStats({
  comparisonType,
  selectedYear,
  selectedDriver1,
  selectedDriver2,
  selectedConstructor1,
  selectedConstructor2,
  drivers,
  constructors,
  useDifferentYears,
  selectedYear1,
  selectedYear2
}) {
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchComparisonData = async () => {
      const baseUrl = fastf1Api.baseUrl.replace(/\/+$/, '');
      if (comparisonType === 'driver-vs-driver' && selectedDriver1 && selectedDriver2) {
        try {
          setLoading(true);
          const response = await fetch(`${baseUrl}/drivers/compare/${selectedDriver1}/${selectedDriver2}`);
          const data = await response.json();
          setComparisonData(data);
        } catch (error) {
          console.error('Error fetching driver comparison:', error);
          setComparisonData(null);
        } finally {
          setLoading(false);
        }
      } else if (comparisonType === 'constructor-vs-constructor' && selectedConstructor1 && selectedConstructor2) {
        try {
          setLoading(true);
          const response = await fetch(`${baseUrl}/constructors/compare/${selectedConstructor1}/${selectedConstructor2}`);
          const data = await response.json();
          setComparisonData(data);
        } catch (error) {
          console.error('Error fetching constructor comparison:', error);
          setComparisonData(null);
        } finally {
          setLoading(false);
        }
      }
    };

    fetchComparisonData();
  }, [comparisonType, selectedDriver1, selectedDriver2, selectedConstructor1, selectedConstructor2]);

  const getDriverName = (driverId) => {
    const driver = drivers.find(d => d.driver_id === parseInt(driverId));
    return driver ? `${driver.first_name} ${driver.last_name}` : 'N/A';
  };

  const getConstructorName = (constructorId) => {
    const constructor = constructors.find(c => c.constructor_id === parseInt(constructorId));
    return constructor?.name || 'N/A';
  };

  const getElo1 = () => {
    if (loading) return '...';
    if (!comparisonData) return '---';
    return comparisonType === 'driver-vs-driver' 
      ? Math.round(comparisonData.driver1?.elo || 0)
      : Math.round(comparisonData.constructor1?.elo || 0);
  };

  const getElo2 = () => {
    if (loading) return '...';
    if (!comparisonData) return '---';
    return comparisonType === 'driver-vs-driver' 
      ? Math.round(comparisonData.driver2?.elo || 0)
      : Math.round(comparisonData.constructor2?.elo || 0);
  };

  const getEloDifference = () => {
    if (loading) return '...';
    if (!comparisonData) return '---';
    const elo1 = comparisonType === 'driver-vs-driver' ? comparisonData.driver1?.elo : comparisonData.constructor1?.elo;
    const elo2 = comparisonType === 'driver-vs-driver' ? comparisonData.driver2?.elo : comparisonData.constructor2?.elo;
    if (!elo1 || !elo2) return '---';
    const diff = Math.round(elo1 - elo2);
    return diff > 0 ? `+${diff}` : diff;
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div className="bg-gradient-to-br from-cyan-500/10 to-cyan-600/10 p-4 rounded-xl border border-cyan-500/20">
        <div className="text-cyan-300 text-xs font-medium mb-1 flex items-center gap-1">
          <span>📊</span>
          <span>Comparison Type</span>
        </div>
        <div className="text-white text-base font-bold truncate">
          {comparisonType === 'driver-vs-driver' ? 'Driver vs Driver' : 'Constructor vs Constructor'}
        </div>
        <div className="text-cyan-300/60 text-xs mt-1">
          {selectedYear}
        </div>
      </div>

      <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 p-4 rounded-xl border border-blue-500/20">
        <div className="text-blue-300 text-xs font-medium mb-1 flex items-center gap-1">
          <span>🏁</span>
          <span>Competitor 1</span>
          {useDifferentYears && <span className="text-blue-400/60">({selectedYear1})</span>}
        </div>
        <div className="text-white text-base font-bold truncate">
          {comparisonType === 'driver-vs-driver' 
            ? getDriverName(selectedDriver1)
            : getConstructorName(selectedConstructor1)}
        </div>
        <div className="text-blue-300/60 text-xs mt-1">
          Elo: {getElo1()}
        </div>
      </div>

      <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 p-4 rounded-xl border border-purple-500/20">
        <div className="text-purple-300 text-xs font-medium mb-1 flex items-center gap-1">
          <span>🏁</span>
          <span>Competitor 2</span>
          {useDifferentYears && <span className="text-purple-400/60">({selectedYear2})</span>}
        </div>
        <div className="text-white text-base font-bold truncate">
          {comparisonType === 'driver-vs-driver' 
            ? getDriverName(selectedDriver2)
            : getConstructorName(selectedConstructor2)}
        </div>
        <div className="text-purple-300/60 text-xs mt-1">
          Elo: {getElo2()}
        </div>
      </div>

      <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 p-4 rounded-xl border border-green-500/20">
        <div className="text-green-300 text-xs font-medium mb-1 flex items-center gap-1">
          <span>⚖️</span>
          <span>Elo Difference</span>
        </div>
        <div className="text-white text-2xl font-bold">
          {getEloDifference()}
        </div>
        <div className="text-green-300/60 text-xs mt-1">
          {!loading && comparisonData && getEloDifference() !== '---' ? (
            getEloDifference() > 0 ? 'Competitor 1 ahead' : 'Competitor 2 ahead'
          ) : 'Loading...'}
        </div>
      </div>
    </div>
  );
}

