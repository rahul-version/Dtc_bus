import React, { useEffect, useState } from 'react';
import { getCorridorDiagnostics, getLiveFleetSummary } from '../services/api';

export default function OperatorDashboard() {
  const [data, setData] = useState(null);
  const [fleet, setFleet] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCorridorDiagnostics(), getLiveFleetSummary()]).then(([diag, flt]) => {
      setData(diag);
      setFleet(flt);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-xs">Loading diagnostics...</div>;
  }

  const corridors = data?.overcrowded_corridors || [];
  const hourly = data?.hourly_network_load || [];

  return (
    <div className="space-y-4">
      {/* 3 Minimal Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white p-3.5 rounded-xl border border-slate-200/70 shadow-xs">
          <div className="text-[11px] font-semibold text-slate-400 uppercase">Live DTC Fleet</div>
          <div className="text-xl font-bold text-slate-900 mt-0.5">
            {fleet?.total_active_buses?.toLocaleString() || '3,597'}
          </div>
          <p className="text-[11px] text-emerald-600 mt-0.5">
            {fleet?.electric_buses_count || 625} Electric (EV) active
          </p>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-slate-200/70 shadow-xs">
          <div className="text-[11px] font-semibold text-slate-400 uppercase">Tickets Modeled</div>
          <div className="text-xl font-bold text-slate-900 mt-0.5">2.56 Million</div>
          <p className="text-[11px] text-slate-500 mt-0.5">October ETM & e-tickets</p>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-slate-200/70 shadow-xs">
          <div className="text-[11px] font-semibold text-slate-400 uppercase">Peak Corridors</div>
          <div className="text-xl font-bold text-slate-900 mt-0.5">138% Load</div>
          <p className="text-[11px] text-rose-600 mt-0.5">+15% Pink Pass factor</p>
        </div>
      </div>

      {/* Clean Corridors Table */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/70 shadow-xs">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold text-xs text-slate-900">Overcrowded Bottleneck Corridors</h3>
          <span className="text-[10px] bg-rose-50 text-rose-700 px-2 py-0.5 rounded font-semibold">
            {corridors.length} Critical
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 text-[11px] uppercase font-semibold">
                <th className="pb-2">Corridor</th>
                <th className="pb-2">Critical Stretch</th>
                <th className="pb-2">Peak Hours</th>
                <th className="pb-2">Peak Load</th>
                <th className="pb-2">Intervention</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {corridors.map((c, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50">
                  <td className="py-2.5 font-medium text-slate-900">{c.corridor_name}</td>
                  <td className="py-2.5 text-slate-600">{c.critical_stretch}</td>
                  <td className="py-2.5 text-slate-500">{c.peak_hour}</td>
                  <td className="py-2.5 font-semibold text-rose-600">{c.average_peak_occupancy}</td>
                  <td className="py-2.5 text-emerald-700">{c.recommendation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slim Daily Graph (IST) */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/70 shadow-xs">
        <div className="flex items-center justify-between mb-3 text-xs">
          <h3 className="font-bold text-slate-900">Daily Network Load Profile (IST)</h3>
          <div className="flex items-center space-x-2 text-[10px] text-slate-500">
            <span>🟢 Normal</span>
            <span>🔴 Crush Peak (&gt;100%)</span>
          </div>
        </div>

        <div className="grid grid-flow-col auto-cols-fr gap-1.5 items-end h-24 px-1">
          {hourly.map((h, i) => {
            const heightPct = Math.min(100, Math.round((h.load_pct / 140) * 100));
            const isPeak = h.load_pct > 100;
            return (
              <div key={i} className="flex flex-col items-center group relative">
                <div
                  style={{ height: `${heightPct}%` }}
                  title={`${h.hour}: ${h.load_pct}% load`}
                  className={`w-full rounded-t-xs transition-all ${
                    isPeak ? 'bg-rose-500 hover:bg-rose-600' : 'bg-emerald-500 hover:bg-emerald-600'
                  }`}
                />
                <span className="text-[8px] text-slate-400 mt-1 whitespace-nowrap">
                  {h.hour_label || h.hour.split(' ')[0]}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
