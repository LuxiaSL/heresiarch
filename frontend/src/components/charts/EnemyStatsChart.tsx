import { useSimQuery } from '../../hooks/useSimQuery';
import { simEnemyStats } from '../../api/client';
import type { EnemyStatsResult } from '../../api/types';
import SimPanel from '../SimPanel';

const STAT_KEYS = ['STR', 'MAG', 'DEF', 'RES', 'SPD'] as const;

export default function EnemyStatsChart() {
  const { data, isLoading, error } = useSimQuery<EnemyStatsResult>('enemy-stats', simEnemyStats, {});

  return (
    <SimPanel
      title="Enemy Stat Profiles"
      subtitle={data ? `${data.enemies.length} enemies across all zones` : undefined}
      isLoading={isLoading}
      error={error?.message}
    >
      {data && data.enemies.map(enemy => (
        <div key={enemy.enemy_id} className="mb-6">
          <div className="mb-2">
            <h3 className="text-base font-semibold text-zinc-100">
              {enemy.enemy_name}
              <span className="ml-2 text-sm font-normal text-zinc-400">
                {enemy.archetype} | budget x{enemy.budget_multiplier.toFixed(1)}
              </span>
            </h3>
            {enemy.equipment.length > 0 && (
              <p className="text-xs text-zinc-500">Equipment: {enemy.equipment.join(', ')}</p>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm text-zinc-300">
              <thead>
                <tr className="border-b border-zinc-700">
                  <th className="text-right py-2 px-2">Zone Lv</th>
                  <th className="text-right py-2 px-2">HP</th>
                  {STAT_KEYS.map(s => (
                    <th key={s} className="text-right py-2 px-2">{s}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {enemy.zone_stats.map(zs => (
                  <tr key={zs.zone_level} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                    <td className="py-1.5 px-2 text-right font-medium">{zs.zone_level}</td>
                    <td className="py-1.5 px-2 text-right font-mono">{zs.hp}</td>
                    {STAT_KEYS.map(s => (
                      <td key={s} className="py-1.5 px-2 text-right font-mono">
                        {zs.base_stats[s] ?? 0}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </SimPanel>
  );
}
