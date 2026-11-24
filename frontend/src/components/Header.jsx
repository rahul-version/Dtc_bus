import React, { useEffect, useState } from 'react';
import { Bus, MapPin, BarChart2 } from 'lucide-react';
import { getLiveFleetSummary } from '../services/api';

export default function Header({ activeTab, setActiveTab }) {
  const [fleetStats, setFleetStats] = useState(null);

  useEffect(() => {
    getLiveFleetSummary().then(setFleetStats);
    const interval = setInterval(() => {
      getLiveFleetSummary().then(setFleetStats);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white border-b border-slate-100 sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center text-white text-sm font-bold">
            <Bus className="w-4 h-4" />
          </div>
          <span className="font-bold text-slate-900 tracking-tight text-base">DTC Saarthi</span>
        </div>

        {/* View Switcher: Minimalist Tab */}
        <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-medium">
          <button
            onClick={() => setActiveTab('commuter')}
            className={`px-3 py-1 rounded-md transition-all ${
              activeTab === 'commuter'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Commuter
          </button>
          <button
            onClick={() => setActiveTab('operator')}
            className={`px-3 py-1 rounded-md transition-all ${
              activeTab === 'operator'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Diagnostics
          </button>
        </div>

        {/* Live GPS Status */}
        <div className="hidden sm:flex items-center space-x-1.5 text-[11px] text-slate-500 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>{fleetStats?.total_active_buses?.toLocaleString() || '3,590'} Live Buses</span>
        </div>
      </div>
    </header>
  );
}
