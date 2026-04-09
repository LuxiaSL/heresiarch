import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simAbilityCompare } from '../../api/client';
import type { AbilityCompareResult } from '../../api/types';
import SimPanel from '../SimPanel';
import JobPicker from '../controls/JobPicker';
import NumberInput from '../controls/NumberInput';

const COLORS = ['#60a5fa', '#f97316', '#a78bfa', '#34d399', '#f472b6', '#facc15'];

export default function AbilityCompareChart() {
  const [jobId, setJobId] = useState('einherjar');
  const [abilityInput, setAbilityInput] = useState('heavy_strike, thrust');
  const [enemyDef, setEnemyDef] = useState(50);

  const abilityIds = abilityInput
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  const params = { job_id: jobId, ability_ids: abilityIds, enemy_def: enemyDef };
  const { data, isLoading, error } = useSimQuery<AbilityCompareResult>(
    'ability-compare',
    simAbilityCompare,
    params,
    abilityIds.length >= 2,
  );

  const chartData = data?.points.map(p => ({
    level: p.level,
    ...p.damages,
  })) ?? [];

  return (
    <SimPanel
      title="Ability Comparison"
      subtitle={data ? `${data.job_id} — ${data.ability_names.join(' vs ')} (DEF=${data.enemy_def})` : undefined}
      isLoading={isLoading}
      error={error?.message}
      controls={<>
        <JobPicker value={jobId} onChange={setJobId} />
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-zinc-400">Ability IDs (comma-separated)</span>
          <input
            type="text"
            value={abilityInput}
            onChange={e => setAbilityInput(e.target.value)}
            placeholder="heavy_strike, thrust"
            className="bg-zinc-800 border border-zinc-600 rounded px-2 py-1 text-zinc-100 w-64"
          />
        </label>
        <NumberInput value={enemyDef} onChange={setEnemyDef} label="Enemy DEF" min={0} max={500} />
      </>}
    >
      {chartData.length > 0 && data && (
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
              label={{ value: 'Damage', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
            />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: '1px solid #4b5563', borderRadius: '8px' }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Legend />
            {data.ability_names.map((name, i) => (
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

      {data && data.crossovers.length > 0 && (
        <div className="mt-4 bg-zinc-800/50 rounded p-4 text-sm">
          <h3 className="font-semibold text-zinc-200 mb-2">Crossover Points</h3>
          {data.crossovers.map((c, i) => (
            <div key={i} className="text-zinc-300">
              <span className="text-blue-400">{c.winner}</span> overtakes{' '}
              <span className="text-orange-400">{c.loser}</span> at Lv{c.level}
              {' '}({c.winner}: {c.winner_value.toFixed(0)}, {c.loser}: {c.loser_value.toFixed(0)})
            </div>
          ))}
        </div>
      )}
    </SimPanel>
  );
}
