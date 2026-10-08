import React, { useState } from 'react';

/**
 * Minimal responsive SVG line chart (the project has no chart library).
 * data: [{ label: string, value: number }]
 */
export const TrendChart = ({ title, data = [], color = '#4f46e5', unit = '', maxValue = null }) => {
  const [hover, setHover] = useState(null);
  const W = 520, H = 180, PAD_L = 40, PAD_R = 12, PAD_T = 12, PAD_B = 28;

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <h4 className="text-sm font-semibold text-slate-800 mb-2">{title}</h4>
        <p className="text-xs text-slate-400 py-10 text-center">No data yet.</p>
      </div>
    );
  }

  const top = maxValue ?? Math.max(1, ...data.map((d) => d.value));
  const bottom = Math.min(0, ...data.map((d) => d.value));
  const span = top - bottom || 1;
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  const x = (i) => PAD_L + (data.length === 1 ? innerW / 2 : (i / (data.length - 1)) * innerW);
  const y = (v) => PAD_T + innerH - ((v - bottom) / span) * innerH;

  const path = data.map((d, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(d.value).toFixed(1)}`).join(' ');
  const ticks = [bottom, bottom + span / 2, top];
  const labelEvery = Math.max(1, Math.ceil(data.length / 6));
  const fmt = (v) => `${Math.round(v * 10) / 10}${unit}`;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-baseline justify-between mb-2">
        <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        <span className="text-xs text-slate-500">
          {hover != null ? `${data[hover].label}: ${fmt(data[hover].value)}` : `Latest: ${fmt(data[data.length - 1].value)}`}
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label={`${title} chart`}>
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={PAD_L} x2={W - PAD_R} y1={y(t)} y2={y(t)} stroke="#e2e8f0" strokeDasharray={i === 0 ? '' : '3 3'} />
            <text x={PAD_L - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fill="#94a3b8">{fmt(t)}</text>
          </g>
        ))}
        <path d={path} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        {data.map((d, i) => (
          <g key={i} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
            <circle cx={x(i)} cy={y(d.value)} r={hover === i ? 5 : 3.5} fill="#fff" stroke={color} strokeWidth="2" />
            {/* larger invisible hit area */}
            <circle cx={x(i)} cy={y(d.value)} r="12" fill="transparent" />
            {i % labelEvery === 0 && (
              <text x={x(i)} y={H - 8} textAnchor="middle" fontSize="10" fill="#94a3b8">{d.label}</text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
};

export default TrendChart;
