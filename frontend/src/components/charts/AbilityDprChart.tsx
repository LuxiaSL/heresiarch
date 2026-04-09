import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simAbilityDpr } from '../../api/client';
import type { AbilityDprResult } from '../../api/types';
import SimPanel from '../SimPanel';
import JobPicker from '../controls/JobPicker';
import NumberInput from '../controls/NumberInput';

const COLORS = ['#60a5fa', '#f97316', '#a78bfa', '#34d399', '#f472b6', '#facc15', '#fb923c', '#38bdf8', '#c084fc', '#4ade80'];

export default function AbilityDprChart() {
  const [jobId, setJobId] = useState('einherjar');
  const [enemyDef, setEnemyDef] = useState(50);

  const params = { job_id: jobId, enemy_def: enemyDef };
  const { data, isLoading, error } = useSimQuery<AbilityDprResult>('ability-dpr', simAbilityDpr, params);

  // Build chart data: one bar group per level, one bar per ability
  const chartData = data?.levels.map(lv => {
    const row: Record<string, unknown> = { level: `Lv${lv}` };
    for (const ability of data.rows) {
      row[ability.ability_name] = ability.damage_by_level[String(lv)] ?? 0;
    }
    return row;
  }) ?? [];

  const abilityNames = data?.rows.map(r => r.ability_name) ?? [];

  return (
    <SimPanel
      title="Ability DPR Analysis"
      subtitle={data ? `${data.job_name} vs DEF=${data.enemy_def}` : undefined}
      isLoading={isLoading}
      error={error?.message}
      controls={<>
        <JobPicker value={jobId} onChange={setJobId} />
        <NumberInput value={enemyDef} onChange={setEnemyDef} label="Enemy DEF" min={0} max={500} />
      </>}
    >
      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="level" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #4b5563', borderRadius: '8px' }} />
            <Legend />
            {abilityNames.slice(0, 10).map((name, i) => (
              <Bar key={name} dataKey={name} fill={COLORS[i % COLORS.length]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      )}

      {data && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm text-zinc-300">
            <thead>
              <tr className="border-b border-zinc-700">
                <th className="text-left py-2 px-2">Ability</th>
                <th className="text-left py-2 px-2">Quality</th>
                <th className="text-left py-2 px-2">Stat</th>
                <th className="text-right py-2 px-2">Coeff</th>
                <th className="text-right py-2 px-2">Unlock</th>
                {data.levels.map(lv => (
                  <th key={lv} className="text-right py-2 px-2">Lv{lv}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map(row => (
                <tr key={row.ability_id} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                  <td className="py-1.5 px-2 font-medium">{row.ability_name}</td>
                  <td className="py-1.5 px-2 text-zinc-400">{row.quality}</td>
                  <td className="py-1.5 px-2 text-zinc-400">{row.scaling_stat}</td>
                  <td className="py-1.5 px-2 text-right">{row.coefficient.toFixed(2)}</td>
                  <td className="py-1.5 px-2 text-right">{row.unlock_level}</td>
                  {data.levels.map(lv => (
                    <td key={lv} className="py-1.5 px-2 text-right font-mono">
                      {row.damage_by_level[String(lv)] ?? '---'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SimPanel>
  );
}
