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

export default function ComparisonGraphPlaceholder({
  comparisonType,
  selectedDriver1,
  selectedDriver2,
  selectedConstructor1,
  selectedConstructor2,
  selectedYear1,
  selectedYear2,
  drivers,
  constructors
}) {
  const [historyData, setHistoryData] = useState({ competitor1: [], competitor2: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchEloHistory = async () => {
      if (comparisonType === 'driver-vs-driver' && selectedDriver1 && selectedDriver2) {
        try {
          setLoading(true);
          
          console.log('Fetching driver Elo history with years:', { selectedYear1, selectedYear2 });
          
          // Fetch Elo history for both drivers
          const [history1Response, history2Response] = await Promise.all([
            fetch(`http://localhost:5001/api/rankings/drivers/elo/history/${selectedDriver1}?season=${selectedYear1}`),
            fetch(`http://localhost:5001/api/rankings/drivers/elo/history/${selectedDriver2}?season=${selectedYear2}`)
          ]);
          
          const history1 = await history1Response.json();
          const history2 = await history2Response.json();
          
          setHistoryData({
            competitor1: history1,
            competitor2: history2
          });
          
          console.log('Driver Elo History Data:', { 
            year1: selectedYear1, 
            year2: selectedYear2,
            history1: history1.length, 
            history2: history2.length 
          });
        } catch (error) {
          console.error('Error fetching driver Elo history:', error);
          setHistoryData({ competitor1: [], competitor2: [] });
        } finally {
          setLoading(false);
        }
      } else if (comparisonType === 'constructor-vs-constructor' && selectedConstructor1 && selectedConstructor2) {
        try {
          setLoading(true);
          
          console.log('Fetching constructor Elo history with years:', { selectedYear1, selectedYear2 });
          
          // Fetch Elo history for both constructors
          const [history1Response, history2Response] = await Promise.all([
            fetch(`http://localhost:5001/api/rankings/constructors/elo/history/${selectedConstructor1}?season=${selectedYear1}`),
            fetch(`http://localhost:5001/api/rankings/constructors/elo/history/${selectedConstructor2}?season=${selectedYear2}`)
          ]);
          
          const history1 = await history1Response.json();
          const history2 = await history2Response.json();
          
          setHistoryData({
            competitor1: history1,
            competitor2: history2
          });
          
          console.log('Constructor Elo History Data:', { 
            year1: selectedYear1, 
            year2: selectedYear2,
            history1: history1.length, 
            history2: history2.length 
          });
        } catch (error) {
          console.error('Error fetching constructor Elo history:', error);
          setHistoryData({ competitor1: [], competitor2: [] });
        } finally {
          setLoading(false);
        }
      }
    };

    fetchEloHistory();
  }, [comparisonType, selectedDriver1, selectedDriver2, selectedConstructor1, selectedConstructor2, selectedYear1, selectedYear2]);

  const getCompetitorName = (id, type) => {
    if (type === 'driver') {
      const driver = drivers.find(d => d.driver_id === parseInt(id));
      return driver ? `${driver.first_name} ${driver.last_name}` : 'Driver';
    } else {
      const constructor = constructors.find(c => c.constructor_id === parseInt(id));
      return constructor?.name || 'Constructor';
    }
  };

  const prepareChartData = () => {
    if (historyData.competitor1.length === 0 && historyData.competitor2.length === 0) return null;

    // Create labels based on the longer history
    const maxLength = Math.max(historyData.competitor1.length, historyData.competitor2.length);
    const labels = Array.from({ length: maxLength }, (_, i) => `R${i + 1}`);

    const competitor1Name = comparisonType === 'driver-vs-driver' 
      ? getCompetitorName(selectedDriver1, 'driver')
      : getCompetitorName(selectedConstructor1, 'constructor');
    
    const competitor2Name = comparisonType === 'driver-vs-driver'
      ? getCompetitorName(selectedDriver2, 'driver')
      : getCompetitorName(selectedConstructor2, 'constructor');

    return {
      labels,
      datasets: [
        {
          label: `${competitor1Name} (${selectedYear1})`,
          data: historyData.competitor1.map(race => race.elo),
          borderColor: '#3B82F6', // Blue
          backgroundColor: '#3B82F620',
          borderWidth: 3,
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: false,
          tension: 0.3
        },
        {
          label: `${competitor2Name} (${selectedYear2})`,
          data: historyData.competitor2.map(race => race.elo),
          borderColor: '#A855F7', // Purple
          backgroundColor: '#A855F720',
          borderWidth: 3,
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: false,
          tension: 0.3
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#fff',
          font: {
            size: 12,
            weight: 'bold'
          },
          padding: 15,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          title: (context) => {
            const race1 = historyData.competitor1[context[0]?.dataIndex];
            const race2 = historyData.competitor2[context[0]?.dataIndex];
            return race1?.race_name || race2?.race_name || context[0]?.label;
          },
          label: (context) => {
            return `${context.dataset.label}: ${Math.round(context.parsed.y)} Elo`;
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
          font: {
            size: 11
          }
        }
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
          drawBorder: false
        },
        ticks: {
          color: '#9CA3AF',
          font: {
            size: 11
          },
          callback: function(value) {
            return Math.round(value);
          }
        },
        title: {
          display: true,
          text: 'Elo Rating',
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

  const chartData = prepareChartData();

  if (loading) {
    return (
      <div className="mb-8">
        <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg shadow-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">📈 Elo Performance Comparison</h2>
          <div className="h-96 flex items-center justify-center bg-gradient-to-br from-black/40 to-black/20 rounded-lg border border-white/10">
            <div className="text-center text-white/60">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
              <div className="text-base">Loading Elo history...</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!chartData || (historyData.competitor1.length === 0 && historyData.competitor2.length === 0)) {
    return (
      <div className="mb-8">
        <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg shadow-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">📈 Elo Performance Comparison</h2>
          <div className="h-96 flex items-center justify-center bg-gradient-to-br from-black/40 to-black/20 rounded-lg border border-white/10">
            <div className="text-center text-white/60">
              <div className="text-6xl mb-4">📊</div>
              <div className="text-xl font-semibold mb-2">No History Data</div>
              <div className="text-sm">Unable to load Elo history for the selected competitors</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg shadow-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center justify-between">
          <span>📈 Elo Performance Comparison</span>
          <span className="text-xs text-white/60">
            {historyData.competitor1.length} races • {historyData.competitor2.length} races
          </span>
        </h2>
        <div className="h-96 bg-gradient-to-br from-black/40 to-black/20 rounded-lg border border-white/10 p-4">
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
}

