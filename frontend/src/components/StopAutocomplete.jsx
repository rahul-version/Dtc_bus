import React, { useState, useEffect, useRef } from 'react';
import { MapPin, X } from 'lucide-react';
import { DELHI_POPULAR_STOPS } from '../services/delhiStops';

export default function StopAutocomplete({
  value,
  onChange,
  placeholder,
  dotColor = 'bg-emerald-500'
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const containerRef = useRef(null);

  useEffect(() => {
    const trimmed = (value || '').trim().toLowerCase();
    if (trimmed.length >= 1) {
      const matches = DELHI_POPULAR_STOPS.filter(stop =>
        stop.toLowerCase().includes(trimmed)
      );
      setSuggestions(matches.slice(0, 8)); // Top 8 matches
      setIsOpen(matches.length > 0);
    } else {
      setSuggestions([]);
      setIsOpen(false);
    }
  }, [value]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, []);

  const handleSelect = (stopName) => {
    onChange(stopName);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative w-full">
      <div className="relative flex items-center">
        {/* Color indicator dot */}
        <span className={`absolute left-3 w-2.5 h-2.5 rounded-full ${dotColor} pointer-events-none`}></span>

        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => {
            const trimmed = (value || '').trim().toLowerCase();
            if (trimmed.length >= 1) {
              const matches = DELHI_POPULAR_STOPS.filter(stop =>
                stop.toLowerCase().includes(trimmed)
              );
              setSuggestions(matches.slice(0, 8));
              setIsOpen(matches.length > 0);
            } else {
              setSuggestions(DELHI_POPULAR_STOPS.slice(0, 8));
              setIsOpen(true);
            }
          }}
          placeholder={placeholder}
          className="w-full pl-8 pr-8 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm font-semibold text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all placeholder:text-slate-400"
          required
          autoComplete="off"
        />

        {/* Clear Button */}
        {value && (
          <button
            type="button"
            onClick={() => onChange('')}
            className="absolute right-2.5 p-1 text-slate-400 hover:text-slate-700 rounded-full"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Autocomplete Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <ul className="absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg z-50 max-h-56 overflow-y-auto divide-y divide-slate-100 py-1">
          {suggestions.map((stop, idx) => (
            <li
              key={idx}
              onMouseDown={() => handleSelect(stop)}
              onTouchStart={() => handleSelect(stop)}
              className="px-3.5 py-2 hover:bg-emerald-50 cursor-pointer flex items-center space-x-2 text-xs font-semibold text-slate-800 transition-colors"
            >
              <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
              <span>{stop}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
