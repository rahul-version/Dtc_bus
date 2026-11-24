import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { getNearbyLiveBuses } from '../services/api';
import { Layers, Radio, Compass } from 'lucide-react';

// Google Maps Transit style crowdedness colors
const CROWD_COLORS = {
  green: { main: '#10b981', border: '#064e3b', label: 'Seats Free' },
  yellow: { main: '#f59e0b', border: '#78350f', label: 'Standing' },
  orange: { main: '#f97316', border: '#7c2d12', label: 'Crowded' },
  red: { main: '#ef4444', border: '#7f1d1d', label: 'Packed' }
};

// Base tile layers (Powered by Google Maps & Transit)
const MAP_MODES = {
  GOOGLE_MAPS: {
    name: 'Google Maps',
    url: 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    maxZoom: 20,
    attribution: '&copy; Google Maps'
  },
  GOOGLE_SATELLITE: {
    name: 'Google Satellite',
    url: 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    maxZoom: 20,
    attribution: '&copy; Google Maps'
  },
  TRANSIT: {
    name: 'Transit Network',
    url: 'https://tile.memomaps.de/tilegen/{z}/{x}/{y}.png',
    maxZoom: 18,
    attribution: '&copy; Public Transport Map'
  }
};

export default function TransitMap({ selectedOption }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const routeLayerRef = useRef(null);
  const liveBusLayerRef = useRef(null);

  const [mapMode, setMapMode] = useState('GOOGLE_MAPS'); // 'GOOGLE_MAPS', 'GOOGLE_SATELLITE', 'TRANSIT'
  const [showLiveBuses, setShowLiveBuses] = useState(false);
  const [liveBuses, setLiveBuses] = useState([]);

  // Fetch real-time buses near route
  useEffect(() => {
    if (!selectedOption || !selectedOption.stretches || selectedOption.stretches.length === 0) return;
    const startStop = selectedOption.stretches[0].from_stop;
    
    getNearbyLiveBuses(startStop).then(setLiveBuses);
    const interval = setInterval(() => {
      getNearbyLiveBuses(startStop).then(setLiveBuses);
    }, 20000);
    return () => clearInterval(interval);
  }, [selectedOption]);

  // Initialize Map with Google Maps Transit Mode tiles
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [28.635, 77.26],
        zoom: 12,
        zoomControl: false,
        attributionControl: false
      });

      // Add Zoom control at bottom right (Google Maps style)
      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // Public Transport Mode Tile Layer
      tileLayerRef.current = L.tileLayer(MAP_MODES.TRANSIT.url, {
        maxZoom: MAP_MODES.TRANSIT.maxZoom,
        attribution: MAP_MODES.TRANSIT.attribution
      }).addTo(map);

      routeLayerRef.current = L.layerGroup().addTo(map);
      liveBusLayerRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }
  }, []);

  // Handle Map Mode switch (Transit vs Street)
  useEffect(() => {
    if (!mapInstanceRef.current || !tileLayerRef.current) return;
    const currentMode = MAP_MODES[mapMode];
    tileLayerRef.current.setUrl(currentMode.url);
  }, [mapMode]);

  // Render Route in Google Maps Transit visual language
  useEffect(() => {
    if (!mapInstanceRef.current || !routeLayerRef.current) return;
    const routeLayer = routeLayerRef.current;
    routeLayer.clearLayers();

    if (!selectedOption || !selectedOption.stretches || selectedOption.stretches.length === 0) return;

    const allCoords = [];
    const totalStretches = selectedOption.stretches.length;

    selectedOption.stretches.forEach((stretch, idx) => {
      const crowdCfg = CROWD_COLORS[stretch.crowding_color] || CROWD_COLORS.green;
      const color = crowdCfg.main;

      // 1. Google Maps Transit Outer Border Stroke (White outline)
      L.polyline([stretch.from_coords, stretch.to_coords], {
        color: '#ffffff',
        weight: 9,
        opacity: 0.95,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(routeLayer);

      // 2. Google Maps Inner Colored Transit Corridor Line
      const poly = L.polyline([stretch.from_coords, stretch.to_coords], {
        color: color,
        weight: 6,
        opacity: 1,
        lineCap: 'round',
        lineJoin: 'round'
      });

      const pct = Math.round(stretch.occupancy_ratio * 100);
      poly.bindPopup(`
        <div style="font-family: inherit; font-size: 12px; padding: 4px;">
          <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
            <span style="font-size: 14px;">🚌</span>
            <strong style="color: #0f172a;">${selectedOption.route_id}</strong>
          </div>
          <div style="color: #334155; font-weight: 500;">${stretch.from_stop} → ${stretch.to_stop}</div>
          <div style="color: ${color}; font-weight: 700; margin-top: 4px;">
            ${stretch.crowding_level.replace('_', ' ')} (${pct}% Full)
          </div>
          <div style="font-size: 11px; color: #64748b; margin-top: 2px;">
            ~${stretch.estimated_passengers} on board • ${stretch.seats_free_estimate} seats free
          </div>
        </div>
      `);

      poly.addTo(routeLayer);
      allCoords.push(stretch.from_coords);
      allCoords.push(stretch.to_coords);

      // 3. Transit Stops: Prominent Google Maps Pinpoints with Station Name Labels
      const isStart = idx === 0;
      if (isStart) {
        // High-contrast Google Maps Origin Pin with floating station name card
        const startIconHtml = `
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            transform: translate(-50%, -100%);
            pointer-events: auto;
            cursor: pointer;
          ">
            <div style="
              background: #0f172a;
              color: #ffffff;
              padding: 5px 12px;
              border-radius: 16px;
              font-size: 11px;
              font-weight: 700;
              white-space: nowrap;
              box-shadow: 0 4px 14px rgba(0,0,0,0.45);
              border: 2px solid #10b981;
              display: flex;
              align-items: center;
              gap: 5px;
              margin-bottom: 2px;
            ">
              <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #10b981; box-shadow: 0 0 6px #10b981;"></span>
              <span>📍 ${stretch.from_stop}</span>
            </div>
            <svg width="24" height="30" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 3px 5px rgba(0,0,0,0.35));">
              <path d="M12 0C5.37 0 0 5.37 0 12C0 19.5 10.5 28.8 11.25 29.47C11.69 29.86 12.31 29.86 12.75 29.47C13.5 28.8 24 19.5 24 12C24 5.37 18.63 0 12 0Z" fill="#10b981"/>
              <circle cx="12" cy="11" r="5" fill="#ffffff"/>
            </svg>
          </div>
        `;
        L.marker(stretch.from_coords, {
          icon: L.divIcon({ html: startIconHtml, className: 'bg-transparent border-0', iconSize: [0, 0], iconAnchor: [0, 0] })
        }).bindPopup(`<strong>📍 Boarding Stop: ${stretch.from_stop}</strong>`).addTo(routeLayer);
      } else {
        // Intermediate Transit Stop Dot with Hover Tooltip
        const stopIconHtml = `
          <div style="
            background: #ffffff;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            border: 2.5px solid #1e293b;
            box-shadow: 0 1px 3px rgba(0,0,0,0.35);
            transform: translate(-50%, -50%);
          "></div>
        `;
        L.marker(stretch.from_coords, {
          icon: L.divIcon({ html: stopIconHtml, className: 'bg-transparent border-0', iconSize: [0, 0], iconAnchor: [0, 0] })
        }).bindTooltip(`🚏 ${stretch.from_stop}`, { direction: 'top', offset: [0, -6] })
          .bindPopup(`<strong>🚏 Transit Stop: ${stretch.from_stop}</strong>`).addTo(routeLayer);
      }

      // Final Destination High-contrast Red Pin with floating station name card
      if (idx === totalStretches - 1) {
        const destIconHtml = `
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            transform: translate(-50%, -100%);
            pointer-events: auto;
            cursor: pointer;
          ">
            <div style="
              background: #0f172a;
              color: #ffffff;
              padding: 5px 12px;
              border-radius: 16px;
              font-size: 11px;
              font-weight: 700;
              white-space: nowrap;
              box-shadow: 0 4px 14px rgba(0,0,0,0.45);
              border: 2px solid #ef4444;
              display: flex;
              align-items: center;
              gap: 5px;
              margin-bottom: 2px;
            ">
              <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #ef4444; box-shadow: 0 0 6px #ef4444;"></span>
              <span>🏁 ${stretch.to_stop}</span>
            </div>
            <svg width="24" height="30" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 3px 5px rgba(0,0,0,0.35));">
              <path d="M12 0C5.37 0 0 5.37 0 12C0 19.5 10.5 28.8 11.25 29.47C11.69 29.86 12.31 29.86 12.75 29.47C13.5 28.8 24 19.5 24 12C24 5.37 18.63 0 12 0Z" fill="#ef4444"/>
              <circle cx="12" cy="11" r="5" fill="#ffffff"/>
            </svg>
          </div>
        `;
        L.marker(stretch.to_coords, {
          icon: L.divIcon({ html: destIconHtml, className: 'bg-transparent border-0', iconSize: [0, 0], iconAnchor: [0, 0] })
        }).bindPopup(`<strong>🏁 Destination: ${stretch.to_stop}</strong>`).addTo(routeLayer);
      }
    });

    if (allCoords.length > 0) {
      mapInstanceRef.current.fitBounds(L.latLngBounds(allCoords), { padding: [35, 35] });
    }
  }, [selectedOption]);

  // Live DTS Real-Time Vehicles
  useEffect(() => {
    if (!mapInstanceRef.current || !liveBusLayerRef.current) return;
    const busLayer = liveBusLayerRef.current;
    busLayer.clearLayers();

    if (!showLiveBuses || liveBuses.length === 0) return;

    liveBuses.forEach((b) => {
      const isEV = b.is_electric;
      const busIconHtml = `
        <div style="
          background-color: ${isEV ? '#0284c7' : '#16a34a'};
          color: white;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          border: 2px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.35);
        ">
          🚌
        </div>
      `;

      const icon = L.divIcon({
        html: busIconHtml,
        className: 'custom-bus-pin',
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });

      L.marker([b.lat, b.lon], { icon })
        .bindPopup(`
          <div style="font-family: inherit; font-size: 11px; padding: 3px; min-width: 160px;">
            <div style="font-weight: bold; color: #0f172a;">${b.vehicle_id}</div>
            <div style="color: ${isEV ? '#0284c7' : '#16a34a'}; font-weight: 600;">
              ${isEV ? '⚡ Electric Zero-Emission' : 'Standard DTC CNG'}
            </div>
            <div style="margin-top: 3px;">Speed: <strong>${b.speed_kmh} km/h</strong></div>
            <div>Distance: <strong>${b.distance_km} km</strong> (~${b.eta_mins}m ETA)</div>
            <div style="font-size: 9px; color: #94a3b8; margin-top: 2px;">Delhi Transport Stack GPS</div>
          </div>
        `)
        .addTo(busLayer);
    });
  }, [liveBuses, showLiveBuses]);

  return (
    <div className="bg-white rounded-xl border border-slate-200/70 p-2.5 shadow-xs flex flex-col h-[440px]">
      {/* Top Transit Mode Header */}
      <div className="flex items-center justify-between mb-2 px-1 text-xs">
        <div className="flex items-center space-x-2">
          {/* Google Maps Mode Badge */}
          <span className="flex items-center space-x-1 font-bold text-slate-800 bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-md border border-emerald-200">
            <span>🗺️</span>
            <span>Google Maps Mode</span>
          </span>
          <span className="text-[11px] text-slate-400 hidden sm:inline">•</span>
          <span className="text-[11px] text-slate-500 font-medium truncate max-w-[170px] hidden sm:inline">
            {selectedOption ? selectedOption.route_name : 'Select Route'}
          </span>
        </div>

        {/* Layer Mode Toggle (Google Maps vs Satellite vs Transit) & Live GPS */}
        <div className="flex items-center space-x-2 text-[11px]">
          <button
            type="button"
            onClick={() => {
              if (mapMode === 'GOOGLE_MAPS') setMapMode('GOOGLE_SATELLITE');
              else if (mapMode === 'GOOGLE_SATELLITE') setMapMode('TRANSIT');
              else setMapMode('GOOGLE_MAPS');
            }}
            className="flex items-center space-x-1 text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 px-2 py-0.5 rounded-md transition-colors font-medium"
            title="Switch Google Maps / Satellite / Transit view"
          >
            <Layers className="w-3 h-3 text-sky-600" />
            <span>
              {mapMode === 'GOOGLE_MAPS' ? 'Google Maps' : mapMode === 'GOOGLE_SATELLITE' ? 'Google Satellite' : 'Transit View'}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setShowLiveBuses(!showLiveBuses)}
            className={`flex items-center space-x-1 px-2 py-0.5 rounded-md font-medium transition-colors ${
              showLiveBuses
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'text-slate-400 bg-slate-50'
            }`}
            title="Toggle Live Realtime Buses"
          >
            <Radio className={`w-3 h-3 ${showLiveBuses ? 'text-emerald-500 animate-pulse' : 'text-slate-400'}`} />
            <span>Live ({liveBuses.length})</span>
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div className="flex-1 w-full rounded-lg overflow-hidden border border-slate-100 relative">
        <div ref={mapContainerRef} className="w-full h-full" />
      </div>

      {/* Google Maps Transit Legend */}
      <div className="flex items-center justify-between pt-2 px-1 text-[11px] font-medium text-slate-500 border-t border-slate-100 mt-2">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span><span>Seats Available</span></span>
          <span className="flex items-center space-x-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span><span>Standing</span></span>
          <span className="flex items-center space-x-1"><span className="w-2.5 h-2.5 rounded-full bg-orange-400"></span><span>Crowded</span></span>
          <span className="flex items-center space-x-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span><span>Packed</span></span>
        </div>
        <div className="text-[10px] text-slate-400 hidden sm:block">
          Metro & Bus corridors visible
        </div>
      </div>
    </div>
  );
}
