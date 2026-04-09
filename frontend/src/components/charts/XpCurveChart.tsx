import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simXpCurve } from '../../api/client';
import type { XpCurveResult } from '../../api/types';
import SimPanel from '../SimPanel';
import JobPicker from '../controls/JobPicker';

export default function XpCurveChart() {
  const [jobId, setJobId] = useState('einherjar');
  const { data, isLoading, error } = useSimQuery<XpCurveResult>('xp-curve', simXpCurve, { job_id: jobId });

  const chartData = data?.zones.map(z => ({
    zone: z.zone_id,
    'Rush': z.level_at_exit_rush,
    'Moderate': z.level_at_exit_moderate,
    'Grind': z.level_at_exit_grind,
    zoneLv: z.zone_level,
  })) ?? [];

  return (
    <SimPanel
      title="XP Progression Curve"
      subtitle={data ? `${data.job_name} — Rush / Moderate (+5 overstay) / Grind (+20 overstay)` : undefined}
      isLoading={isLoading}
      error={error?.message}
      controls={<JobPicker value={jobId} onChange={setJobId} />}
    >
      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="zone" stroke="#9ca3af" angle={-30} textAnchor="end" height={60} tick={{ fontSize: 11 }} />
            <YAxis stroke="#9ca3af" label={{ value: 'Player Level', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
            <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #4b5563', borderRadius: '8px' }} />
            <Legend />
            <Line type="monotone" dataKey="Rush" stroke="#60a5fa" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Moderate" stroke="#34d399" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Grind" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      )}

      {data && data.milestones.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <h3 className="font-semibold text-zinc-200 mb-2">Milestone Zones</h3>
          <table className="w-full text-sm text-zinc-300">
            <thead><tr className="border-b border-zinc-700">
              <th className="text-right py-2 px-2">Level</th>
              <th className="text-left py-2 px-2">Rush</th>
              <th className="text-left py-2 px-2">Moderate</th>
              <th className="text-left py-2 px-2">Grind</th>
            </tr></thead>
            <tbody>
              {data.milestones.map(m => (
                <tr key={m.target_level} className="border-b border-zinc-800">
                  <td className="py-1 px-2 text-right font-medium">Lv{m.target_level}</td>
                  <td className="py-1 px-2">{m.rush_zone}</td>
                  <td className="py-1 px-2">{m.moderate_zone}</td>
                  <td className="py-1 px-2">{m.grind_zone}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SimPanel>
  );
}
