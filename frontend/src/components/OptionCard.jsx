import React from 'react';
import { formatToIST } from '../services/api';
import { MapPin, Armchair, Users, AlertCircle } from 'lucide-react';

// Super simple, friendly status (Easy for anyone to understand)
const SIMPLE_CROWD = {
  SEATS_AVAILABLE: {
    badge: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    dot: 'bg-emerald-500',
    title: '🟢 Seats Available (Khali Bus)',
    icon: Armchair
  },
  STANDING_ROOM: {
    badge: 'bg-amber-100 text-amber-800 border-amber-300',
    dot: 'bg-amber-500',
    title: '🟡 Standing Room (Normal)',
    icon: Users
  },
  CROWDED: {
    badge: 'bg-orange-100 text-orange-800 border-orange-300',
    dot: 'bg-orange-500',
    title: '🟠 Heavy Rush (Bheed Hai)',
    icon: AlertCircle
  },
  PACKED: {
    badge: 'bg-rose-100 text-rose-800 border-rose-300',
    dot: 'bg-rose-500',
    title: '🔴 Full Packed (Bohot Bheed)',
    icon: AlertCircle
  }
};

const STRETCH_COLORS = {
  green: 'bg-emerald-500',
  yellow: 'bg-amber-400',
  orange: 'bg-orange-400',
  red: 'bg-rose-500'
};

export default function OptionCard({ option, isSelected, onSelect }) {
  const crowd = SIMPLE_CROWD[option.overall_crowding_level] || SIMPLE_CROWD.STANDING_ROOM;
  const IconComp = crowd.icon;

  return (
    <div
      onClick={onSelect}
      className={`bg-white rounded-2xl border transition-all cursor-pointer p-4 space-y-3 select-none active:scale-[0.99] ${
        isSelected
          ? 'border-emerald-500 ring-2 ring-emerald-500/20 shadow-md'
          : 'border-slate-200/80 hover:border-slate-300 shadow-xs'
      }`}
    >
      {/* 1. Main Header: Big Bus Route & Simple Crowding Badge */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          {/* Bus Route Pill */}
          <span className="font-extrabold text-white bg-slate-900 px-2.5 py-1 rounded-lg text-xs tracking-tight">
            Bus {option.route_id ? option.route_id.replace(/^Bus\s*/i, '') : 'DTC'}
          </span>
          {option.is_ac ? (
            <span className="text-[10px] font-bold text-sky-700 bg-sky-100 px-2 py-0.5 rounded-md">
              AC
            </span>
          ) : (
            <span className="text-[10px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded-md">
              Non-AC
            </span>
          )}
          <span className="font-bold text-slate-800 text-xs">
            ₹{option.fare_inr}
          </span>
        </div>

        {/* Big Simple Crowding Badge */}
        <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border text-xs font-bold ${crowd.badge}`}>
          <IconComp className="w-3.5 h-3.5 shrink-0" />
          <span>{crowd.title}</span>
        </div>
      </div>

      {/* Route Badge Subtitle / Feature */}
      {option.badge_label && (
        <div className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-md w-fit">
          ✨ {option.badge_label}
        </div>
      )}

      {/* 2. Timing & Duration Row */}
      <div className="flex items-center justify-between text-slate-900 pt-1">
        <div>
          <span className="text-base font-extrabold">
            {formatToIST(option.departure_time)} → {formatToIST(option.arrival_time)}
          </span>
        </div>
        <div className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg">
          ⏱️ Takes {option.duration_minutes} mins
        </div>
      </div>

      {/* 3. Simple Visual Stretch Bar (Green = Khali, Red = Packed) */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px] font-medium text-slate-400">
          <span>{option.stretches?.[0]?.from_stop}</span>
          <span>Crowd along stops</span>
          <span>{option.stretches?.[option.stretches.length - 1]?.to_stop}</span>
        </div>
        <div className="grid grid-flow-col auto-cols-fr gap-1 h-2.5 w-full rounded-full overflow-hidden bg-slate-100 p-0.5">
          {option.stretches?.map((s, idx) => {
            const barClass = STRETCH_COLORS[s.crowding_color] || 'bg-slate-300';
            return (
              <div
                key={idx}
                title={`${s.from_stop} → ${s.to_stop}: ${s.crowding_level}`}
                className={`h-full rounded-full ${barClass}`}
              />
            );
          })}
        </div>
      </div>

      {/* 4. Helpful Commuter Tip */}
      <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-xs text-slate-600">
        <span className="truncate pr-2 font-medium">
          💡 {option.commuter_advice || 'Comfortable journey'}
        </span>
        <button
          type="button"
          className="text-emerald-600 font-bold text-xs flex items-center space-x-1 shrink-0 hover:underline"
        >
          <MapPin className="w-3 h-3" />
          <span>View Map</span>
        </button>
      </div>
    </div>
  );
}
