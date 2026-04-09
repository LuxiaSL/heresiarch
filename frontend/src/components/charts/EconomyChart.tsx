import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simEconomy } from '../../api/client';
import type { EconomyResult } from '../../api/types';
import SimPanel from '../SimPanel';

export default function EconomyChart() {
  const { data, isLoading, error } = useSimQuery<EconomyResult>('economy', simEconomy, {});

  const chartData = data?.zones.map(z => ({
    zone: z.zone_name.length > 15 ? z.zone_id : z.zone_name,
    'Zone Gold': Math.round(z.zone_gold),
    'Rush (cumulative)': Math.round(z.cumulative_gold_rush),
    'Moderate (cumulative)': Math.round(z.cumulative_gold_moderate),
    'Grind (cumulative)': Math.round(z.cumulative_gold_grind),
  })) ?? [];

  return (
    <SimPanel title="Zone Economy" subtitle="Gold flow across zones by play style" isLoading={isLoading} error={error?.message}>
      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="zone" stroke="#9ca3af" angle={-30} textAnchor="end" height={60} tick={{ fontSize: 11 }} />
            <YAxis stroke="#9ca3af" />
            <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #4b5563', borderRadius: '8px' }} />
            <Legend />
            <Line type="monotone" dataKey="Zone Gold" stroke="#facc15" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Rush (cumulative)" stroke="#60a5fa" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Moderate (cumulative)" stroke="#34d399" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Grind (cumulative)" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      )}

      {data && data.pilfer_impacts.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <h3 className="font-semibold text-zinc-200 mb-2">Pilfer Impact ({data.pilfer_flat}G flat + {data.pilfer_per_level}G/level)</h3>
          <table className="w-full text-sm text-zinc-300">
            <thead><tr className="border-b border-zinc-700">
              <th className="text-left py-2 px-2">Zone</th>
              <th className="text-right py-2 px-2">Zone Gold</th>
              <th className="text-right py-2 px-2">Per Hit</th>
              <th className="text-right py-2 px-2">2 Hits</th>
              <th className="text-right py-2 px-2">Enc. Equiv</th>
            </tr></thead>
            <tbody>
              {data.pilfer_impacts.map(p => (
                <tr key={p.zone_id} className="border-b border-zinc-800">
                  <td className="py-1 px-2">{p.zone_id}</td>
                  <td className="py-1 px-2 text-right font-mono">{p.zone_gold.toFixed(0)}G</td>
                  <td className="py-1 px-2 text-right font-mono">{p.pilfer_per_hit}G</td>
                  <td className="py-1 px-2 text-right font-mono">{p.two_hits}G</td>
                  <td className="py-1 px-2 text-right font-mono">{p.encounter_equivalent.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SimPanel>
  );
}
