import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simWeaponSweep, simCrossovers } from '../../api/client';
import type { WeaponSweepResult, CrossoverResult } from '../../api/types';
import SimPanel from '../SimPanel';
import JobPicker from '../controls/JobPicker';
import StatPicker from '../controls/StatPicker';

const COLORS = ['#60a5fa', '#f97316', '#a78bfa', '#34d399', '#f472b6', '#facc15'];

export default function WeaponSweepChart() {
  const [jobId, setJobId] = useState('einherjar');
  const [stat, setStat] = useState('STR');

  const params = { job_id: jobId, stat };
  const sweep = useSimQuery<WeaponSweepResult>('weapon-sweep', simWeaponSweep, params);
  const cross = useSimQuery<CrossoverResult>('crossovers', simCrossovers, params);

  const data = sweep.data?.points.map(p => ({
    level: p.level,
    ...p.outputs,
  })) ?? [];

  return (
    <SimPanel
      title="Weapon Scaling Sweep"
      subtitle={sweep.data ? `${sweep.data.stat} growth: +${sweep.data.growth_rate}/lv` : undefined}
      isLoading={sweep.isLoading}
      error={sweep.error?.message}
      controls={<>
        <JobPicker value={jobId} onChange={setJobId} />
        <StatPicker value={stat} onChange={setStat} />
      </>}
    >
      {data.length > 0 && (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="level" stroke="#9ca3af" label={{ value: 'Level', position: 'bottom', fill: '#9ca3af' }} />
            <YAxis stroke="#9ca3af" label={{ value: 'Scaling Output', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: '1px solid #4b5563', borderRadius: '8px' }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Legend />
            {sweep.data?.weapon_names.map((name, i) => (
              <Line key={name} type="monotone" dataKey={name} stroke={COLORS[i % COLORS.length]}
                strokeWidth={2} dot={{ r: 3 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}

      {cross.data && (cross.data.crossovers.length > 0 || cross.data.breakevens.length > 0) && (
        <div className="mt-4 bg-zinc-800/50 rounded p-4 text-sm">
          <h3 className="font-semibold text-zinc-200 mb-2">Crossover Analysis</h3>
          {cross.data.crossovers.map((c, i) => (
            <div key={i} className="text-zinc-300">
              <span className="text-blue-400">{c.winner}</span> overtakes{' '}
              <span className="text-orange-400">{c.loser}</span> at Lv{c.level}
              {' '}({c.winner}: {c.winner_value.toFixed(0)}, {c.loser}: {c.loser_value.toFixed(0)})
            </div>
          ))}
          {cross.data.breakevens.map((b, i) => (
            <div key={`b${i}`} className="text-zinc-300">
              <span className="text-purple-400">{b.weapon}</span> breaks even at Lv{b.level}
              {' '}(stat={b.stat_value}, output={b.output})
            </div>
          ))}
        </div>
      )}
    </SimPanel>
  );
}
