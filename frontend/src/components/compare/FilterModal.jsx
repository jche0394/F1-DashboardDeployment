import React, { useState, useMemo, useEffect } from 'react';
import ToggleSwitch from '../shared/ToggleSwitch';
import fastf1Api from '../../services/api';
import SearchableSelector from '../shared/SearchableSelector';
import YearSelector from '../shared/YearSelector';
import SectionHeader from '../shared/SectionHeader';

export default function FilterModal({ 
  isOpen, 
  onClose, 
  selectedYear, 
  setSelectedYear, 
  comparisonType, 
  setComparisonType,
  drivers,
  constructors,
  selectedDriver1,
  setSelectedDriver1,
  selectedDriver2,
  setSelectedDriver2,
  selectedConstructor1,
  setSelectedConstructor1,
  selectedConstructor2,
  setSelectedConstructor2,
  useDifferentYears,
  setUseDifferentYears,
  selectedYear1,
  setSelectedYear1,
  selectedYear2,
  setSelectedYear2
}) {
  const [driverSearch1, setDriverSearch1] = useState('');
  const [driverSearch2, setDriverSearch2] = useState('');
  const [constructorSearch1, setConstructorSearch1] = useState('');
  const [constructorSearch2, setConstructorSearch2] = useState('');
  const [drivers1, setDrivers1] = useState([]);
  const [drivers2, setDrivers2] = useState([]);
  const [constructors1, setConstructors1] = useState([]);
  const [constructors2, setConstructors2] = useState([]);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: currentYear - 1949 }, (_, i) => currentYear - i);

  // Fetch data for year 1
  useEffect(() => {
    const fetchDataForYear1 = async () => {
      try {
        const baseUrl = fastf1Api.baseUrl.replace(/\/+$/, '');
        const driverResponse = await fetch(`${baseUrl}/rankings/drivers/elo?season=${selectedYear1}`);
        const driverData = await driverResponse.json();
        setDrivers1(driverData.slice(0, 50));

        const combinedResponse = await fetch(`${baseUrl}/rankings/combined?season=${selectedYear1}`);
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
        setConstructors1(uniqueConstructors.slice(0, 20));
      } catch (err) {
        console.error('Error fetching data for year 1:', err);
      }
    };

    fetchDataForYear1();
  }, [selectedYear1]);

  // Fetch data for year 2
  useEffect(() => {
    const fetchDataForYear2 = async () => {
      try {
        const baseUrl = fastf1Api.baseUrl.replace(/\/+$/, '');
        const driverResponse = await fetch(`${baseUrl}/rankings/drivers/elo?season=${selectedYear2}`);
        const driverData = await driverResponse.json();
        setDrivers2(driverData.slice(0, 50));

        const combinedResponse = await fetch(`${baseUrl}/rankings/combined?season=${selectedYear2}`);
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
        setConstructors2(uniqueConstructors.slice(0, 20));
      } catch (err) {
        console.error('Error fetching data for year 2:', err);
      }
    };

    fetchDataForYear2();
  }, [selectedYear2]);

  // Prepare driver data for SearchableSelector
  const driverData1 = useMemo(() => {
    const driverList = useDifferentYears ? drivers1 : drivers;
    return driverList.map(driver => ({
      id: driver.driver_id,
      name: `${driver.first_name} ${driver.last_name}`,
      code: driver.code
    }));
  }, [useDifferentYears, drivers1, drivers]);

  const driverData2 = useMemo(() => {
    const driverList = useDifferentYears ? drivers2 : drivers;
    return driverList.map(driver => ({
      id: driver.driver_id,
      name: `${driver.first_name} ${driver.last_name}`,
      code: driver.code
    }));
  }, [useDifferentYears, drivers2, drivers]);

  // Filter drivers based on search
  const filteredDrivers1 = useMemo(() => {
    if (!driverSearch1) return driverData1.slice(0, 10);
    return driverData1.filter(driver => 
      driver.name.toLowerCase().includes(driverSearch1.toLowerCase())
    ).slice(0, 10);
  }, [driverData1, driverSearch1]);

  const filteredDrivers2 = useMemo(() => {
    if (!driverSearch2) return driverData2.slice(0, 10);
    return driverData2.filter(driver => 
      driver.name.toLowerCase().includes(driverSearch2.toLowerCase())
    ).slice(0, 10);
  }, [driverData2, driverSearch2]);

  // Prepare constructor data for SearchableSelector
  const constructorData1 = useMemo(() => {
    const constructorList = useDifferentYears ? constructors1 : constructors;
    return constructorList.map(constructor => ({
      id: constructor.constructor_id,
      name: constructor.name
    }));
  }, [useDifferentYears, constructors1, constructors]);

  const constructorData2 = useMemo(() => {
    const constructorList = useDifferentYears ? constructors2 : constructors;
    return constructorList.map(constructor => ({
      id: constructor.constructor_id,
      name: constructor.name
    }));
  }, [useDifferentYears, constructors2, constructors]);

  // Filter constructors based on search
  const filteredConstructors1 = useMemo(() => {
    if (!constructorSearch1) return constructorData1.slice(0, 10);
    return constructorData1.filter(constructor => 
      constructor.name.toLowerCase().includes(constructorSearch1.toLowerCase())
    ).slice(0, 10);
  }, [constructorData1, constructorSearch1]);

  const filteredConstructors2 = useMemo(() => {
    if (!constructorSearch2) return constructorData2.slice(0, 10);
    return constructorData2.filter(constructor => 
      constructor.name.toLowerCase().includes(constructorSearch2.toLowerCase())
    ).slice(0, 10);
  }, [constructorData2, constructorSearch2]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
      <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <span className="p-2 bg-blue-500/20 rounded-lg">
                <span className="text-blue-400">⚙️</span>
              </span>
              Configure Comparison
            </h2>
            <p className="text-gray-400 mt-1">Customize your comparison settings and filters</p>
          </div>
          <button
            onClick={onClose}
            className="p-3 hover:bg-white/10 rounded-lg transition-all duration-200 text-gray-400 hover:text-white hover:scale-105"
          >
            <span className="text-xl">✕</span>
          </button>
        </div>


        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh] custom-scrollbar">
          <div className="space-y-8">
            {/* Season & Year Selection */}
            <div>
              <SectionHeader icon="📅" title="Season Selection" />
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <YearSelector
                    label="Base Year"
                    value={selectedYear}
                    onChange={setSelectedYear}
                    years={years}
                  />
                  
                  <div className="flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <div className="text-2xl mb-2">🏁</div>
                      <p className="text-sm">Select a year to view F1 data</p>
                    </div>
                  </div>
                </div>
                
                <ToggleSwitch
                  isOn={useDifferentYears}
                  onToggle={() => setUseDifferentYears(!useDifferentYears)}
                  label="Use different years"
                  description={`Allow selecting ${comparisonType === 'driver-vs-driver' ? 'drivers' : 'constructors'} from different seasons`}
                />
                
                {useDifferentYears && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <YearSelector
                      label={`Year for ${comparisonType === 'driver-vs-driver' ? 'Driver' : 'Constructor'} A`}
                      value={selectedYear1}
                      onChange={setSelectedYear1}
                      years={years}
                    />
                    <YearSelector
                      label={`Year for ${comparisonType === 'driver-vs-driver' ? 'Driver' : 'Constructor'} B`}
                      value={selectedYear2}
                      onChange={setSelectedYear2}
                      years={years}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Comparison Type */}
            <div>
              <SectionHeader icon="🔍" title="Comparison Type" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => setComparisonType('driver-vs-driver')}
                  className={`p-6 rounded-lg border-2 transition-all text-left ${
                    comparisonType === 'driver-vs-driver'
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-gray-600 bg-gray-800 hover:border-gray-500'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">🏎️</span>
                    <h4 className="font-semibold text-white">Driver vs Driver</h4>
                  </div>
                  <p className="text-sm text-gray-400">
                    Compare individual driver performances, Elo ratings, and career stats
                  </p>
                </button>

                <button
                  onClick={() => setComparisonType('constructor-vs-constructor')}
                  className={`p-6 rounded-lg border-2 transition-all text-left ${
                    comparisonType === 'constructor-vs-constructor'
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-gray-600 bg-gray-800 hover:border-gray-500'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">🏁</span>
                    <h4 className="font-semibold text-white">Constructor vs Constructor</h4>
                  </div>
                  <p className="text-sm text-gray-400">
                    Compare team performances, constructor Elo ratings, and team statistics
                  </p>
                </button>
              </div>
            </div>

            {/* Driver Selection */}
            {comparisonType === 'driver-vs-driver' && (
              <div>
                <SectionHeader 
                  icon="🏎️" 
                  title="Driver Selection"
                  subtitle={useDifferentYears ? `(A: ${selectedYear1}, B: ${selectedYear2})` : null}
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <SearchableSelector
                    label="Select Driver A"
                    placeholder="Search drivers..."
                    searchValue={driverSearch1}
                    onSearchChange={setDriverSearch1}
                    items={filteredDrivers1}
                    selectedValue={selectedDriver1}
                    onSelect={(id) => {
                      setSelectedDriver1(id);
                      setDriverSearch1('');
                    }}
                    selectedColor="blue"
                    showCode={false}
                    emptyMessage="No drivers found"
                  />
                  
                  <SearchableSelector
                    label="Select Driver B"
                    placeholder="Search drivers..."
                    searchValue={driverSearch2}
                    onSearchChange={setDriverSearch2}
                    items={filteredDrivers2}
                    selectedValue={selectedDriver2}
                    onSelect={(id) => {
                      setSelectedDriver2(id);
                      setDriverSearch2('');
                    }}
                    selectedColor="red"
                    showCode={false}
                    emptyMessage="No drivers found"
                  />
                </div>
              </div>
            )}

            {/* Constructor Selection */}
            {comparisonType === 'constructor-vs-constructor' && (
              <div>
                <SectionHeader 
                  icon="🏁" 
                  title="Constructor Selection"
                  subtitle={useDifferentYears ? `(A: ${selectedYear1}, B: ${selectedYear2})` : null}
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <SearchableSelector
                    label="Select Constructor A"
                    placeholder="Search constructors..."
                    searchValue={constructorSearch1}
                    onSearchChange={setConstructorSearch1}
                    items={filteredConstructors1}
                    selectedValue={selectedConstructor1}
                    onSelect={(id) => {
                      setSelectedConstructor1(id);
                      setConstructorSearch1('');
                    }}
                    selectedColor="blue"
                    showCode={false}
                    emptyMessage="No constructors found"
                  />
                  
                  <SearchableSelector
                    label="Select Constructor B"
                    placeholder="Search constructors..."
                    searchValue={constructorSearch2}
                    onSearchChange={setConstructorSearch2}
                    items={filteredConstructors2}
                    selectedValue={selectedConstructor2}
                    onSelect={(id) => {
                      setSelectedConstructor2(id);
                      setConstructorSearch2('');
                    }}
                    selectedColor="red"
                    showCode={false}
                    emptyMessage="No constructors found"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-white/10">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 text-gray-300">
              <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
              <span>Current: {selectedYear}</span>
            </div>
            <div className="flex items-center gap-2 text-gray-300">
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              <span>{comparisonType === 'driver-vs-driver' ? 'Driver vs Driver' : 'Constructor vs Constructor'}</span>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-6 py-3 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-all duration-200 font-medium"
            >
              Cancel
            </button>
            <button
              onClick={onClose}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-500 hover:to-blue-600 transition-all duration-200 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              Apply Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
