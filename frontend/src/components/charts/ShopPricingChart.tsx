import { useSimQuery } from '../../hooks/useSimQuery';
import { simShopPricing } from '../../api/client';
import type { ShopPricingResult } from '../../api/types';
import SimPanel from '../SimPanel';

function affordColor(value: string): string {
  switch (value.toUpperCase()) {
    case 'YES': return 'text-green-400';
    case 'NO': return 'text-red-400';
    default: return 'text-zinc-300';
  }
}

function potionStatusColor(status: string): string {
  switch (status.toUpperCase()) {
    case 'OK': return 'text-green-400';
    case 'CHEAP': return 'text-yellow-400';
    case 'EXPENSIVE': return 'text-red-400';
    default: return 'text-zinc-300';
  }
}

export default function ShopPricingChart() {
  const { data, isLoading, error } = useSimQuery<ShopPricingResult>('shop-pricing', simShopPricing, {});

  return (
    <SimPanel
      title="Shop Pricing Analysis"
      subtitle="Affordability by zone and potion pricing health"
      isLoading={isLoading}
      error={error?.message}
    >
      {data && data.zones.length > 0 && (
        <div className="space-y-6">
          <div>
            <h3 className="font-semibold text-zinc-200 mb-2">Shop Affordability by Zone</h3>
            {data.zones.map(zone => (
              <div key={zone.zone_name} className="mb-4">
                <div className="text-sm text-zinc-400 mb-1">
                  {zone.zone_name} (Lv{zone.zone_level})
                  <span className="ml-2 text-zinc-500">
                    Gold — Rush: {Math.round(zone.cumulative_gold_rush)}G
                    | Mod: {Math.round(zone.cumulative_gold_moderate)}G
                    | Grind: {Math.round(zone.cumulative_gold_grind)}G
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-zinc-300">
                    <thead>
                      <tr className="border-b border-zinc-700">
                        <th className="text-left py-1.5 px-2">Item</th>
                        <th className="text-right py-1.5 px-2">Base</th>
                        <th className="text-right py-1.5 px-2">Buy</th>
                        <th className="text-right py-1.5 px-2">% Rush</th>
                        <th className="text-right py-1.5 px-2">% Mod</th>
                        <th className="text-right py-1.5 px-2">% Grind</th>
                        <th className="text-center py-1.5 px-2">Affordable</th>
                      </tr>
                    </thead>
                    <tbody>
                      {zone.items.map(item => (
                        <tr key={item.item_id} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                          <td className="py-1 px-2">{item.item_name}</td>
                          <td className="py-1 px-2 text-right font-mono">{item.base_price}G</td>
                          <td className="py-1 px-2 text-right font-mono">{item.buy_price}G</td>
                          <td className="py-1 px-2 text-right font-mono">
                            {item.pct_rush != null ? `${item.pct_rush.toFixed(0)}%` : '---'}
                          </td>
                          <td className="py-1 px-2 text-right font-mono">
                            {item.pct_moderate != null ? `${item.pct_moderate.toFixed(0)}%` : '---'}
                          </td>
                          <td className="py-1 px-2 text-right font-mono">
                            {item.pct_grind != null ? `${item.pct_grind.toFixed(0)}%` : '---'}
                          </td>
                          <td className={`py-1 px-2 text-center font-semibold ${affordColor(item.affordable)}`}>
                            {item.affordable}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>

          {data.potions.length > 0 && (
            <div>
              <h3 className="font-semibold text-zinc-200 mb-2">Potion Pricing Check</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-zinc-300">
                  <thead>
                    <tr className="border-b border-zinc-700">
                      <th className="text-left py-2 px-2">Potion</th>
                      <th className="text-right py-2 px-2">Base</th>
                      <th className="text-right py-2 px-2">Buy</th>
                      <th className="text-left py-2 px-2">Intro Zone</th>
                      <th className="text-right py-2 px-2">Avg Enc. Gold</th>
                      <th className="text-right py-2 px-2">Ratio</th>
                      <th className="text-center py-2 px-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.potions.map(p => (
                      <tr key={p.potion_id} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                        <td className="py-1.5 px-2">{p.potion_name}</td>
                        <td className="py-1.5 px-2 text-right font-mono">{p.base_price}G</td>
                        <td className="py-1.5 px-2 text-right font-mono">{p.buy_price}G</td>
                        <td className="py-1.5 px-2">{p.intro_zone ?? '---'}</td>
                        <td className="py-1.5 px-2 text-right font-mono">
                          {p.avg_encounter_gold != null ? `${p.avg_encounter_gold.toFixed(0)}G` : '---'}
                        </td>
                        <td className="py-1.5 px-2 text-right font-mono">
                          {p.ratio != null ? p.ratio.toFixed(2) : '---'}
                        </td>
                        <td className={`py-1.5 px-2 text-center font-semibold ${potionStatusColor(p.status)}`}>
                          {p.status}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </SimPanel>
  );
}
