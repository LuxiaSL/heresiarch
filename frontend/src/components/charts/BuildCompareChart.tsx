import { useState } from 'react';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simBuildCompare } from '../../api/client';
import type { BuildCompareResult } from '../../api/types';
import SimPanel from '../SimPanel';
import JobPicker from '../controls/JobPicker';
import NumberInput from '../controls/NumberInput';

const STAT_KEYS = ['STR', 'MAG', 'DEF', 'RES', 'SPD'] as const;

export default function BuildCompareChart() {
  const [jobId, setJobId] = useState('einherjar');
  const [level, setLevel] = useState(50);

  const params = { job_id: jobId, level };
  const { data, isLoading, error } = useSimQuery<BuildCompareResult>('build-compare', simBuildCompare, params);

  const hasDamage = data?.builds.some(b => b.heavy_damage != null || b.bolt_damage != null || b.dpt != null) ?? false;

  return (
    <SimPanel
      title="Build Comparison"
      subtitle={data ? `${data.job_id} at Lv${data.level}${data.enemy_info ? ` — ${data.enemy_info}` : ''}` : undefined}
      isLoading={isLoading}
      error={error?.message}
      controls={<>
        <JobPicker value={jobId} onChange={setJobId} />
        <NumberInput value={level} onChange={setLevel} label="Level" min={1} max={99} />
      </>}
    >
      {data && data.builds.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-zinc-300">
            <thead>
              <tr className="border-b border-zinc-700">
                <th className="text-left py-2 px-2">Build</th>
                {STAT_KEYS.map(s => (
                  <th key={s} className="text-right py-2 px-2">{s}</th>
                ))}
                <th className="text-right py-2 px-2">HP</th>
                <th className="text-right py-2 px-2">Bonus Act.</th>
                {hasDamage && <>
                  <th className="text-right py-2 px-2">Heavy</th>
                  <th className="text-right py-2 px-2">Bolt</th>
                  <th className="text-right py-2 px-2">DPT</th>
                </>}
              </tr>
            </thead>
            <tbody>
              {data.builds.map(b => (
                <tr key={b.name} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                  <td className="py-1.5 px-2 font-medium">{b.name}</td>
                  {STAT_KEYS.map(s => (
                    <td key={s} className="py-1.5 px-2 text-right font-mono">
                      {b.stats[s] ?? 0}
                    </td>
                  ))}
                  <td className="py-1.5 px-2 text-right font-mono">{b.hp}</td>
                  <td className="py-1.5 px-2 text-right font-mono">{b.bonus_actions}</td>
                  {hasDamage && <>
                    <td className="py-1.5 px-2 text-right font-mono">
                      {b.heavy_damage != null ? b.heavy_damage.toFixed(0) : '---'}
                    </td>
                    <td className="py-1.5 px-2 text-right font-mono">
                      {b.bolt_damage != null ? b.bolt_damage.toFixed(0) : '---'}
                    </td>
                    <td className="py-1.5 px-2 text-right font-mono">
                      {b.dpt != null ? b.dpt.toFixed(0) : '---'}
                    </td>
                  </>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SimPanel>
  );
}
