import { useState } from 'react';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simProgression } from '../../api/client';
import type { ProgressionResult } from '../../api/types';
import SimPanel from '../SimPanel';
import JobPicker from '../controls/JobPicker';

export default function ProgressionChart() {
  const [jobId, setJobId] = useState('einherjar');

  const params = { job_id: jobId };
  const { data, isLoading, error } = useSimQuery<ProgressionResult>('progression', simProgression, params);

  return (
    <SimPanel
      title="Full Progression Timeline"
      subtitle={data ? `${data.job_name} — ${data.primary_stat} +${data.growth_rate}/lv` : undefined}
      isLoading={isLoading}
      error={error?.message}
      controls={<JobPicker value={jobId} onChange={setJobId} />}
    >
      {data && data.zones.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-zinc-300">
            <thead>
              <tr className="border-b border-zinc-700">
                <th className="text-left py-2 px-2">Zone</th>
                <th className="text-right py-2 px-2">Lv</th>
                <th className="text-right py-2 px-2">Exit Rush</th>
                <th className="text-right py-2 px-2">Exit Mod</th>
                <th className="text-right py-2 px-2">Exit Grind</th>
                <th className="text-right py-2 px-2">Gold (R/M/G)</th>
                <th className="text-left py-2 px-2">Best Weapon</th>
                <th className="text-left py-2 px-2">Affordable Items</th>
                <th className="text-left py-2 px-2">Unlocked Abilities</th>
              </tr>
            </thead>
            <tbody>
              {data.zones.map(z => (
                <tr key={z.zone_id} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                  <td className="py-1.5 px-2 font-medium">{z.zone_name}</td>
                  <td className="py-1.5 px-2 text-right">{z.zone_level}</td>
                  <td className="py-1.5 px-2 text-right font-mono">{z.exit_level_rush}</td>
                  <td className="py-1.5 px-2 text-right font-mono">{z.exit_level_moderate}</td>
                  <td className="py-1.5 px-2 text-right font-mono">{z.exit_level_grind}</td>
                  <td className="py-1.5 px-2 text-right font-mono text-xs">
                    {Math.round(z.cumulative_gold_rush)} / {Math.round(z.cumulative_gold_moderate)} / {Math.round(z.cumulative_gold_grind)}
                  </td>
                  <td className="py-1.5 px-2 text-blue-400">
                    {z.best_weapon ?? '---'}
                  </td>
                  <td className="py-1.5 px-2 text-xs">
                    {z.affordable_items.length > 0
                      ? z.affordable_items.join(', ')
                      : <span className="text-zinc-500">none</span>
                    }
                  </td>
                  <td className="py-1.5 px-2 text-xs">
                    {z.unlocked_abilities.length > 0
                      ? z.unlocked_abilities.join(', ')
                      : <span className="text-zinc-500">none</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SimPanel>
  );
}
