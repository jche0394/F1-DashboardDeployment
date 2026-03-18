import React, { useState, useEffect } from "react";
import FilterModal from '../components/compare/FilterModal';
import fastf1Api from '../services/api';
import ComparisonSummaryStats from '../components/compare/ComparisonSummaryStats';
import ComparisonEmptyState from '../components/compare/ComparisonEmptyState';
import ComparisonGraphPlaceholder from '../components/compare/ComparisonGraphPlaceholder';
import ComparisonInfoCards from '../components/compare/ComparisonInfoCards';
import SyncStatus from '../components/layout/SyncStatus';

export default function ComparePage() {
  const [drivers, setDrivers] = useState([]);
  const [constructors, setConstructors] = useState([]);
  const [selectedDriver1, setSelectedDriver1] = useState('');
  const [selectedDriver2, setSelectedDriver2] = useState('');
  const [selectedConstructor1, setSelectedConstructor1] = useState('');
  const [selectedConstructor2, setSelectedConstructor2] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [comparisonType, setComparisonType] = useState('driver-vs-driver'); // 'driver-vs-driver', 'constructor-vs-constructor'
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear()); // Default to current year
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [useDifferentYears, setUseDifferentYears] = useState(false);
  const [selectedYear1, setSelectedYear1] = useState(new Date().getFullYear());
  const [selectedYear2, setSelectedYear2] = useState(new Date().getFullYear());

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch drivers for selected year using the existing endpoint
        const driverResponse = await fetch(`${fastf1Api.baseUrl}/rankings/drivers/elo?season=${selectedYear}`);
        const driverData = await driverResponse.json();
        setDrivers(driverData.slice(0, 50)); // Top 50 drivers for dropdown
        
        // Fetch constructors from combined rankings
        const combinedResponse = await fetch(`${fastf1Api.baseUrl}/rankings/combined?season=${selectedYear}`);
        const combinedData = await combinedResponse.json();
        const uniqueConstructors = combinedData.reduce((acc, entry) => {
          if (!acc.find(c => c.constructor_id === entry.constructor_id)) {
            acc.push({
              constructor_id: entry.constructor_id,
              name: entry.constructor_name
            });
          }
          return acc;
        }, []);
        setConstructors(uniqueConstructors.slice(0, 20)); // Top 20 constructors
        
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load data. Please check if the backend server is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedYear]);

  useEffect(() => {
    setSelectedDriver1('');
    setSelectedDriver2('');
    setSelectedConstructor1('');
    setSelectedConstructor2('');
    // Sync year1 and year2 with selectedYear when not using different years
    if (!useDifferentYears) {
      setSelectedYear1(selectedYear);
      setSelectedYear2(selectedYear);
    }
  }, [selectedYear, useDifferentYears]);


  if (loading) {
    return (
      <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 text-white bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
            Compare Performance
          </h1>
          <p className="text-lg text-white/70 max-w-4xl mx-auto">
            Head-to-head analysis of drivers and constructors using Elo ratings and performance metrics
          </p>
        </div>
        <div className="text-center text-white/60">Loading comparison data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 text-white bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
            Compare Performance
          </h1>
          <p className="text-lg text-white/70 max-w-4xl mx-auto">
            Head-to-head analysis of drivers and constructors using Elo ratings and performance metrics
          </p>
        </div>
        <div className="text-center p-6 bg-red-500/10 rounded-xl border border-red-500/20">
          <div className="text-red-400 text-lg font-semibold mb-2">Error Loading Data</div>
          <div className="text-red-300">{error}</div>
        </div>
      </div>
    );
  }

  const hasSelections = (comparisonType === 'driver-vs-driver' && selectedDriver1 && selectedDriver2) ||
                      (comparisonType === 'constructor-vs-constructor' && selectedConstructor1 && selectedConstructor2);

  return (
    <div className="pt-28 p-6 font-sans text-gray-200 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 text-white bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
          Compare Performance
        </h1>
        <p className="text-lg text-white/70 max-w-4xl mx-auto">
          Head-to-head analysis of drivers and constructors using Elo ratings and performance metrics
        </p>
      </div>

      {/* Configure Button - Always visible */}
      <div className="flex justify-center mb-8">
        <button
          onClick={() => setIsFilterModalOpen(true)}
          className="group relative px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white rounded-xl transition-all duration-200 shadow-lg hover:shadow-2xl transform hover:scale-105 font-semibold"
        >
          {hasSelections ? '⚙️ Change Comparison' : 'Select competitors to compare'}
        </button>
      </div>

      {/* Information Cards - When no selection */}
      {!hasSelections && <ComparisonInfoCards />}

      {/* Filter Modal */}
      <FilterModal
        isOpen={isFilterModalOpen}
        onClose={() => setIsFilterModalOpen(false)}
        selectedYear={selectedYear}
        setSelectedYear={setSelectedYear}
        comparisonType={comparisonType}
        setComparisonType={setComparisonType}
        drivers={drivers}
        constructors={constructors}
        selectedDriver1={selectedDriver1}
        setSelectedDriver1={setSelectedDriver1}
        selectedDriver2={selectedDriver2}
        setSelectedDriver2={setSelectedDriver2}
        selectedConstructor1={selectedConstructor1}
        setSelectedConstructor1={setSelectedConstructor1}
        selectedConstructor2={selectedConstructor2}
        setSelectedConstructor2={setSelectedConstructor2}
        useDifferentYears={useDifferentYears}
        setUseDifferentYears={setUseDifferentYears}
        selectedYear1={selectedYear1}
        setSelectedYear1={setSelectedYear1}
        selectedYear2={selectedYear2}
        setSelectedYear2={setSelectedYear2}
      />

      {/* Summary Stats - Shows when selections are made */}
      {hasSelections && (
        <ComparisonSummaryStats
          comparisonType={comparisonType}
          selectedYear={selectedYear}
          selectedDriver1={selectedDriver1}
          selectedDriver2={selectedDriver2}
          selectedConstructor1={selectedConstructor1}
          selectedConstructor2={selectedConstructor2}
          drivers={drivers}
          constructors={constructors}
          useDifferentYears={useDifferentYears}
          selectedYear1={selectedYear1}
          selectedYear2={selectedYear2}
        />
      )}

      {/* Elo Comparison Graph - Empty Container for Future Implementation */}
      {hasSelections && (
        <ComparisonGraphPlaceholder
          comparisonType={comparisonType}
          selectedDriver1={selectedDriver1}
          selectedDriver2={selectedDriver2}
          selectedConstructor1={selectedConstructor1}
          selectedConstructor2={selectedConstructor2}
          selectedYear1={selectedYear1}
          selectedYear2={selectedYear2}
          drivers={drivers}
          constructors={constructors}
        />
      )}

      {/* Empty State - When no selections made */}
      {!hasSelections && <ComparisonEmptyState />}

      {/* Footer Sync Info */}
      <div className="mt-6">
        <SyncStatus />
      </div>
    </div>
  );
}
