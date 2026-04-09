import { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simConverter } from '../../api/client';
import type { ConverterCompareResult } from '../../api/types';
import { useItems } from '../../hooks/useGameData';
import SimPanel from '../SimPanel';
import JobPicker from '../controls/JobPicker';

const COLORS = ['#60a5fa', '#f97316', '#a78bfa', '#34d399', '#f472b6', '#facc15'];

export default function ConverterChart() {
  const [jobId, setJobId] = useState('martyr');
  const [converterId, setConverterId] = useState('fortress_ring');

  const { data: items } = useItems();

  const converterItems = useMemo(() => {
    if (!items) return [];
    return Object.values(items).filter(it => it.has_conversion);
  }, [items]);

  const params = { job_id: jobId, converter_id: converterId };
  const { data, isLoading, error } = useSimQuery<ConverterCompareResult>(
    'converter',
    simConverter,
    params,
  );

  const converterNames = data ? Object.keys(data.points[0]?.outputs ?? {}) : [];

  const chartData = data?.points.map(p => ({
    level: p.level,
    ...p.outputs,
  })) ?? [];

  return (
    <SimPanel
      title="Converter Comparison"
      subtitle={data ? `${data.job_id} — ${data.source_stat} -> ${data.target_stat} (growth ${data.growth_rate}/lv)` : undefined}
      isLoading={isLoading}
      error={error?.message}
      controls={<>
        <JobPicker value={jobId} onChange={setJobId} />
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-zinc-400">Converter</span>
          <select
            value={converterId}
            onChange={e => setConverterId(e.target.value)}
            className="bg-zinc-800 border border-zinc-600 rounded px-2 py-1 text-zinc-100"
          >
            {converterItems.length > 0
              ? converterItems.map(it => (
                  <option key={it.id} value={it.id}>{it.name}</option>
                ))
              : <option value={converterId}>{converterId}</option>
            }
          </select>
        </label>
      </>}
    >
      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="level"
              stroke="#9ca3af"
              label={{ value: 'Level', position: 'bottom', fill: '#9ca3af' }}
            />
            <YAxis
              stroke="#9ca3af"
              label={{ value: 'Converter Output', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
            />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: '1px solid #4b5563', borderRadius: '8px' }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Legend />
            {converterNames.map((name, i) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </SimPanel>
  );
}
