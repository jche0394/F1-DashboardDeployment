import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import fastf1Api from '../../services/api.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function PointsHistoryChart() {
  const [pointsData, setPointsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDrivers, setSelectedDrivers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [quickFilter, setQuickFilter] = useState('top3'); // 'top3', 'top5', 'top10', 'all'
  const [availableDrivers, setAvailableDrivers] = useState([]);

  // Color palette for driver lines
  const driverColors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
    '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2',
    '#A9DFBF', '#F9E79F', '#D5DBDB', '#AED6F1', '#FADBD8'
  ];

  useEffect(() => {
    const fetchPointsHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await fastf1Api.getPointsHistory();
        setPointsData(data);
        
        // Get all available drivers and sort by final points
        if (data.pointsHistory && data.pointsHistory.length > 0) {
          const finalStandings = data.pointsHistory[data.pointsHistory.length - 1].standings;
          setAvailableDrivers(finalStandings.map(standing => standing.driver));
          
          // Default to top 3 drivers by final points
          const topDrivers = finalStandings.slice(0, 3).map(standing => standing.driver);
          setSelectedDrivers(topDrivers);
        }
      } catch (err) {
        console.error('Error fetching points history:', err);
        setError('Failed to load points history data');
      } finally {
        setLoading(false);
      }
    };

    fetchPointsHistory();
  }, []);

  // Apply quick filter
  useEffect(() => {
    if (!pointsData || !pointsData.pointsHistory || pointsData.pointsHistory.length === 0) return;
    
    // Don't apply quick filter if it's set to 'custom' - let user maintain their selection
    if (quickFilter === 'custom') return;
    
    const finalStandings = pointsData.pointsHistory[pointsData.pointsHistory.length - 1].standings;
    
    let filteredDrivers = [];
    if (quickFilter === 'top3') {
      filteredDrivers = finalStandings.slice(0, 3).map(s => s.driver);
    } else if (quickFilter === 'top5') {
      filteredDrivers = finalStandings.slice(0, 5).map(s => s.driver);
    } else if (quickFilter === 'top10') {
      filteredDrivers = finalStandings.slice(0, 10).map(s => s.driver);
    } else if (quickFilter === 'all') {
      filteredDrivers = finalStandings.map(s => s.driver);
    }
    
    setSelectedDrivers(filteredDrivers);
  }, [quickFilter, pointsData]);


  const prepareChartData = () => {
    if (!pointsData || !pointsData.pointsHistory) return null;

    const rounds = pointsData.pointsHistory.map(race => `R${race.round}`);
    const datasets = selectedDrivers.map((driverName, index) => {
      const points = pointsData.pointsHistory.map(race => {
        const driverStanding = race.standings.find(standing => standing.driver === driverName);
        return driverStanding ? driverStanding.points : 0;
      });

      return {
        label: driverName,
        data: points,
        borderColor: driverColors[index % driverColors.length],
        backgroundColor: driverColors[index % driverColors.length] + '20',
        borderWidth: 3,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: false,
        tension: 0.1
      };
    });

    return {
      labels: rounds,
      datasets: datasets
    };
  };

  const toggleDriver = (driverName) => {
    setSelectedDrivers(prev => {
      if (prev.includes(driverName)) {
        return prev.filter(d => d !== driverName);
      } else {
        return [...prev, driverName];
      }
    });
    setQuickFilter('custom'); // Switch to custom when manually toggling
  };

  const filteredDriversForSearch = availableDrivers.filter(driver =>
    driver.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false // Hide default legend, we'll use custom driver selector
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        cornerRadius: 8,
        titleFont: {
          size: 14,
          weight: 'bold'
        },
        bodyFont: {
          size: 13
        },
        callbacks: {
          title: (context) => {
            const raceIndex = context[0]?.dataIndex;
            if (pointsData?.pointsHistory?.[raceIndex]) {
              return pointsData.pointsHistory[raceIndex].raceName || `Round ${context[0]?.label}`;
            }
            return context[0]?.label;
          },
          label: (context) => {
            const points = context.parsed.y;
            return `${context.dataset.label}: ${points} pts`;
          },
          afterBody: (context) => {
            return ''; // Remove extra clutter
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          drawBorder: false
        },
        ticks: {
          color: '#9CA3AF',
          font: { size: 11 }
        }
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          drawBorder: false
        },
        ticks: {
          color: '#9CA3AF',
          font: { size: 11 }
        },
        title: {
          display: true,
          text: 'Points',
          color: '#9CA3AF',
          font: {
            size: 12,
            weight: 'bold'
          }
        }
      }
    },
    interaction: {
      mode: 'index',
      intersect: false
    }
  };

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/30 mx-auto mb-2"></div>
          <div className="text-sm">Loading points history...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="text-center text-red-400">
          <div className="text-4xl mb-2">📉</div>
          <div className="text-sm">{error}</div>
        </div>
      </div>
    );
  }

  if (!pointsData || !pointsData.pointsHistory || pointsData.pointsHistory.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="text-4xl mb-2">📊</div>
          <div className="text-sm">No points history data available</div>
        </div>
      </div>
    );
  }

  const chartData = prepareChartData();
  if (!chartData) return null;

  return (
    <div className="h-full w-full flex flex-col">
      {/* Filters Section */}
      <div className="mb-4 space-y-3">
        {/* Quick Filters and Search in one row */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-white/60 text-xs font-medium mr-1">Quick Filter:</span>
          <button
            onClick={() => setQuickFilter('top3')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              quickFilter === 'top3'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            Top 3
          </button>
          <button
            onClick={() => setQuickFilter('top5')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              quickFilter === 'top5'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            Top 5
          </button>
          <button
            onClick={() => setQuickFilter('top10')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              quickFilter === 'top10'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            Top 10
          </button>
          <button
            onClick={() => setQuickFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              quickFilter === 'all'
                ? 'bg-blue-500 text-white shadow-lg'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setQuickFilter('custom')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              quickFilter === 'custom'
                ? 'bg-purple-500 text-white shadow-lg'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            Custom
          </button>
          
          <div className="h-4 w-px bg-white/20 mx-1"></div>
          
          <input
            type="text"
            placeholder="Search drivers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-1.5 bg-white/10 border border-white/20 rounded-lg text-white text-xs placeholder-white/40 focus:outline-none focus:border-blue-500 focus:bg-white/15 transition-all min-w-[150px]"
          />
          
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-400 hover:text-red-300 text-xs transition-all border border-red-500/30"
            >
              Clear
            </button>
          )}
          
          <span className="text-white/40 text-xs ml-2">
            {selectedDrivers.length} selected
          </span>
          
          {selectedDrivers.length > 0 && (
            <button
              onClick={() => {
                setSelectedDrivers([]);
                setQuickFilter('top3');
              }}
              className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-400 hover:text-red-300 text-xs transition-all border border-red-500/30 ml-2"
            >
              Clear All
            </button>
          )}
        </div>

        {/* Driver Selection Pills - Only show when searching */}
        {searchQuery && (
          <div className="max-h-24 overflow-y-auto custom-scrollbar">
            <div className="flex flex-wrap gap-2">
              {(searchQuery ? filteredDriversForSearch : availableDrivers).slice(0, 20).map((driver) => {
                const isSelected = selectedDrivers.includes(driver);
                const colorIndex = availableDrivers.indexOf(driver);
                const driverColor = driverColors[colorIndex % driverColors.length];
                
                return (
                  <button
                    key={driver}
                    onClick={() => toggleDriver(driver)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                      isSelected
                        ? 'text-white shadow-lg border-2'
                        : 'bg-white/10 text-white/60 hover:bg-white/20 border border-white/20'
                    }`}
                    style={isSelected ? {
                      backgroundColor: driverColor + '30',
                      borderColor: driverColor
                    } : {}}
                  >
                    {driver}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0">
        <Line data={chartData} options={chartOptions} />
      </div>
    </div>
  );
}