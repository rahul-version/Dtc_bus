import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import JourneySearch from './components/JourneySearch';
import OptionCard from './components/OptionCard';
import TransitMap from './components/TransitMap';
import OperatorDashboard from './components/OperatorDashboard';
import { planJourney, formatToIST } from './services/api';
import { ListFilter, Map as MapIcon } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('commuter'); // 'commuter' | 'operator'
  const [fromStop, setFromStop] = useState('Anand Vihar ISBT');
  const [toStop, setToStop] = useState('Connaught Place (Shivaji Stadium)');
  const [time, setTime] = useState('18:00');
  const [day, setDay] = useState('weekday');
  const [preference, setPreference] = useState('balanced');
  const [journeyResult, setJourneyResult] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Mobile active screen: 'cards' or 'map'
  const [mobileView, setMobileView] = useState('cards');

  useEffect(() => {
    handleSearch();
  }, [preference]);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const data = await planJourney({
        fromStop,
        toStop,
        departureTime: time,
        dayOfWeek: day,
        preference
      });
      setJourneyResult(data);
      if (data.options && data.options.length > 0) {
        setSelectedOption(data.options[0]);
      }
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (opt) => {
    setSelectedOption(opt);
    // On mobile, if commuter clicks a card, show them the map
    if (window.innerWidth < 1024) {
      setMobileView('map');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/70 flex flex-col font-sans pb-16 lg:pb-0">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-3 sm:px-4 py-3 sm:py-4">
        {activeTab === 'commuter' ? (
          <div className="space-y-3">
            {/* Minimal Input Bar */}
            <JourneySearch
              fromStop={fromStop}
              setFromStop={setFromStop}
              toStop={toStop}
              setToStop={setToStop}
              time={time}
              setTime={setTime}
              day={day}
              setDay={setDay}
              preference={preference}
              setPreference={setPreference}
              onSearch={handleSearch}
              loading={loading}
            />

            {/* Mobile View Toggle Switch (List vs Map) */}
            <div className="lg:hidden flex items-center bg-slate-200/70 p-1 rounded-xl text-xs font-semibold">
              <button
                type="button"
                onClick={() => setMobileView('cards')}
                className={`flex-1 py-1.5 rounded-lg flex items-center justify-center space-x-1.5 transition-all ${
                  mobileView === 'cards'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600'
                }`}
              >
                <ListFilter className="w-3.5 h-3.5" />
                <span>Available Trips ({journeyResult?.options?.length || 0})</span>
              </button>
              <button
                type="button"
                onClick={() => setMobileView('map')}
                className={`flex-1 py-1.5 rounded-lg flex items-center justify-center space-x-1.5 transition-all ${
                  mobileView === 'map'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600'
                }`}
              >
                <MapIcon className="w-3.5 h-3.5 text-sky-600" />
                <span>Transit Map</span>
              </button>
            </div>

            {/* Split Grid: Side-by-side on desktop, Toggled view on mobile */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-start">
              {/* Left Column: Journey Cards */}
              <div className={`lg:col-span-6 space-y-2 ${mobileView === 'map' ? 'hidden lg:block' : 'block'}`}>
                <div className="hidden lg:flex items-center justify-between px-1 text-xs text-slate-500 font-medium">
                  <span>Available Trips at {formatToIST(time)}</span>
                  <span>Select card to view route</span>
                </div>

                {loading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="bg-white rounded-xl p-4 border border-slate-200/60 animate-pulse space-y-2">
                        <div className="h-4 bg-slate-100 rounded w-1/3"></div>
                        <div className="h-2 bg-slate-100 rounded w-full"></div>
                      </div>
                    ))}
                  </div>
                ) : journeyResult?.options?.length > 0 ? (
                  <div className="space-y-2">
                    {journeyResult.options.map((opt) => (
                      <OptionCard
                        key={opt.option_id}
                        option={opt}
                        isSelected={selectedOption?.option_id === opt.option_id}
                        onSelect={() => handleSelectOption(opt)}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="bg-white p-6 rounded-xl border border-slate-200 text-center text-slate-500 text-xs">
                    No routes found. Select a preset or check stop names.
                  </div>
                )}
              </div>

              {/* Right Column: Interactive Map */}
              <div className={`lg:col-span-6 lg:sticky lg:top-16 ${mobileView === 'cards' ? 'hidden lg:block' : 'block'}`}>
                <TransitMap selectedOption={selectedOption} />
              </div>
            </div>
          </div>
        ) : (
          <OperatorDashboard />
        )}
      </main>

      <footer className="border-t border-slate-200/60 bg-white py-3 text-center text-[11px] text-slate-400 hidden sm:block">
        DTC Saarthi • Delhi Transport Stack Crowdedness Planner
      </footer>
    </div>
  );
}
