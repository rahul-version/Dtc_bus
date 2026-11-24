import React from 'react';
import { ArrowRightLeft, Clock, Search, Plus, Minus } from 'lucide-react';
import StopAutocomplete from './StopAutocomplete';
import { formatToIST } from '../services/api';

const QUICK_TIMES = [
  { label: '⚡ Abhi (Now)', getValue: () => {
    const d = new Date();
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  }},
  { label: '8:30 AM (Morning)', value: '08:30' },
  { label: '1:00 PM (Noon)', value: '13:00' },
  { label: '6:00 PM (Evening)', value: '18:00' },
  { label: '9:00 PM (Night)', value: '21:00' }
];

function adjustTimeMinutes(timeStr, deltaMinutes) {
  try {
    const [h, m] = timeStr.split(':').map(Number);
    const total = (h * 60 + m + deltaMinutes + 1440) % 1440;
    const newH = Math.floor(total / 60);
    const newM = total % 60;
    return `${String(newH).padStart(2, '0')}:${String(newM).padStart(2, '0')}`;
  } catch {
    return '18:00';
  }
}

export default function JourneySearch({
  fromStop,
  setFromStop,
  toStop,
  setToStop,
  time,
  setTime,
  day,
  setDay,
  preference,
  setPreference,
  onSearch,
  loading
}) {
  const handleSwap = () => {
    const temp = fromStop;
    setFromStop(toStop);
    setToStop(temp);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-3.5 sm:p-4 shadow-sm space-y-3">
      {/* 1. Origin & Destination Inputs with 2-Letter Instant Dropdown */}
      <form onSubmit={(e) => { e.preventDefault(); onSearch(); }} className="space-y-2.5">
        <div className="relative space-y-2">
          {/* Boarding Stop */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Start Station (From)
            </label>
            <StopAutocomplete
              value={fromStop}
              onChange={setFromStop}
              placeholder="Search boarding stop (e.g. Anand Vihar, AIIMS...)"
              dotColor="bg-emerald-500"
            />
          </div>

          {/* Swap Button (Floating) */}
          <button
            type="button"
            onClick={handleSwap}
            className="absolute right-3 top-[52px] z-10 p-2 text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-full shadow-md active:scale-90 transition-all"
            title="Swap stations"
          >
            <ArrowRightLeft className="w-3.5 h-3.5" />
          </button>

          {/* Destination Stop */}
          <div>
            <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Stop Station (To)
            </label>
            <StopAutocomplete
              value={toStop}
              onChange={setToStop}
              placeholder="Search destination stop (e.g. Connaught Place, Kashmere Gate...)"
              dotColor="bg-rose-500"
            />
          </div>
        </div>

        {/* 2. No-Keyboard Time Picker (One-Tap Stepper & Chips) */}
        <div className="bg-slate-50 rounded-xl p-2.5 border border-slate-200/60 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5 text-xs text-slate-700 font-semibold">
              <Clock className="w-3.5 h-3.5 text-emerald-600" />
              <span>Travel Time:</span>
              <span className="bg-white px-2 py-0.5 rounded-md border border-slate-200 text-emerald-700 font-bold text-xs">
                {formatToIST(time)}
              </span>
            </div>

            {/* Quick -15m / +15m buttons (No keyboard needed!) */}
            <div className="flex items-center space-x-1">
              <button
                type="button"
                onClick={() => setTime(adjustTimeMinutes(time, -15))}
                className="px-2 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg text-xs font-bold active:scale-95 transition-all flex items-center space-x-0.5"
                title="15 min pehle"
              >
                <Minus className="w-3 h-3" />
                <span>15m</span>
              </button>
              <button
                type="button"
                onClick={() => setTime(adjustTimeMinutes(time, 15))}
                className="px-2 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg text-xs font-bold active:scale-95 transition-all flex items-center space-x-0.5"
                title="15 min baad"
              >
                <Plus className="w-3 h-3" />
                <span>15m</span>
              </button>
            </div>
          </div>

          {/* Quick Tap Time Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto whitespace-nowrap pb-0.5 no-scrollbar">
            {QUICK_TIMES.map((qt, i) => {
              const val = qt.value || (qt.getValue ? qt.getValue() : '18:00');
              const isActive = time === val;
              return (
                <button
                  key={i}
                  type="button"
                  onClick={() => setTime(val)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all shrink-0 ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : 'bg-white hover:bg-slate-100 text-slate-600 border border-slate-200/80'
                  }`}
                >
                  {qt.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 3. Search Action Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] text-white py-3 px-4 rounded-xl text-sm font-bold shadow-md transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          {loading ? (
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          ) : (
            <>
              <Search className="w-4 h-4" />
              <span>Show Best Bus Options</span>
            </>
          )}
        </button>
      </form>

      {/* 4. Preference Filter (Seats First vs Fastest) */}
      <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-xs">
        <span className="text-[11px] font-semibold text-slate-400">Sort:</span>
        <div className="flex items-center space-x-1">
          <button
            type="button"
            onClick={() => setPreference('fastest')}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
              preference === 'fastest' ? 'bg-slate-900 text-white' : 'text-slate-600 bg-slate-100'
            }`}
          >
            ⚡ Fastest
          </button>
          <button
            type="button"
            onClick={() => setPreference('comfortable')}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
              preference === 'comfortable' ? 'bg-emerald-600 text-white' : 'text-slate-600 bg-slate-100'
            }`}
          >
            💺 Seats Available
          </button>
          <button
            type="button"
            onClick={() => setPreference('balanced')}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
              preference === 'balanced' ? 'bg-slate-900 text-white' : 'text-slate-600 bg-slate-100'
            }`}
          >
            ⚖️ Balanced
          </button>
        </div>
      </div>
    </div>
  );
}
