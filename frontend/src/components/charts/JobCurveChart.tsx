import { useState } from 'react';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simJobCurve } from '../../api/client';
import type { JobCurveResult } from '../../api/types';
import SimPanel from '../SimPanel';
import JobPicker from '../controls/JobPicker';
import NumberInput from '../controls/NumberInput';

export default function JobCurveChart() {
  const [jobId, setJobId] = useState('einherjar');
  const [enemyDef, setEnemyDef] = useState(50);

  const params = { job_id: jobId, enemy_def: enemyDef };
  const { data, isLoading, error } = useSimQuery<JobCurveResult>('job-curve', simJobCurve, params);

  return (
    <SimPanel
      title="Job Power Curve"
      subtitle={data ? `${data.job_name} vs DEF=${data.enemy_def}` : undefined}
      isLoading={isLoading}
      error={error?.message}
      controls={<>
        <JobPicker value={jobId} onChange={setJobId} />
        <NumberInput value={enemyDef} onChange={setEnemyDef} label="Enemy DEF" min={0} max={500} />
      </>}
    >
      {data && data.unlocks.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-zinc-300">
            <thead>
              <tr className="border-b border-zinc-700">
                <th className="text-right py-2 px-2">Unlock Lv</th>
                <th className="text-left py-2 px-2">Ability</th>
                <th className="text-left py-2 px-2">Category</th>
                <th className="text-left py-2 px-2">Quality</th>
                <th className="text-left py-2 px-2">Stat</th>
                <th className="text-right py-2 px-2">Damage @ Unlock</th>
                <th className="text-right py-2 px-2">vs Basic</th>
              </tr>
            </thead>
            <tbody>
              {data.unlocks.map(u => (
                <tr key={u.ability_id} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                  <td className="py-1.5 px-2 text-right font-medium">{u.unlock_level}</td>
                  <td className="py-1.5 px-2 font-medium">{u.ability_name}</td>
                  <td className="py-1.5 px-2 text-zinc-400">{u.category}</td>
                  <td className="py-1.5 px-2 text-zinc-400">{u.quality}</td>
                  <td className="py-1.5 px-2 text-zinc-400">{u.scaling_stat}</td>
                  <td className="py-1.5 px-2 text-right font-mono">{u.damage_at_unlock.toFixed(0)}</td>
                  <td className="py-1.5 px-2 text-right font-mono">
                    <span className={u.ratio_vs_basic >= 1.5 ? 'text-green-400' : u.ratio_vs_basic >= 1.0 ? 'text-zinc-300' : 'text-red-400'}>
                      {u.ratio_vs_basic.toFixed(2)}x
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && (data.strongest_unlock || data.first_power_spike) && (
        <div className="mt-4 bg-zinc-800/50 rounded p-4 text-sm space-y-1">
          {data.strongest_unlock && (
            <div className="text-zinc-300">
              <span className="text-zinc-400">Strongest unlock:</span>{' '}
              <span className="text-green-400 font-medium">{data.strongest_unlock}</span>
            </div>
          )}
          {data.first_power_spike && (
            <div className="text-zinc-300">
              <span className="text-zinc-400">First power spike:</span>{' '}
              <span className="text-blue-400 font-medium">{data.first_power_spike}</span>
            </div>
          )}
        </div>
      )}
    </SimPanel>
  );
}
