import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import WeaponSweepChart from './components/charts/WeaponSweepChart';
import AbilityDprChart from './components/charts/AbilityDprChart';
import AbilityCompareChart from './components/charts/AbilityCompareChart';
import JobCurveChart from './components/charts/JobCurveChart';
import BuildCompareChart from './components/charts/BuildCompareChart';
import ConverterChart from './components/charts/ConverterChart';
import SigmoidChart from './components/charts/SigmoidChart';
import EconomyChart from './components/charts/EconomyChart';
import XpCurveChart from './components/charts/XpCurveChart';
import EnemyStatsChart from './components/charts/EnemyStatsChart';
import ShopPricingChart from './components/charts/ShopPricingChart';
import ProgressionChart from './components/charts/ProgressionChart';
import FormulaEditor from './components/config/FormulaEditor';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const PANELS: Record<string, React.ComponentType> = {
  'weapon-sweep': WeaponSweepChart,
  'ability-dpr': AbilityDprChart,
  'ability-compare': AbilityCompareChart,
  'job-curve': JobCurveChart,
  'build-compare': BuildCompareChart,
  'converter': ConverterChart,
  'sigmoid': SigmoidChart,
  'economy': EconomyChart,
  'xp-curve': XpCurveChart,
  'enemy-stats': EnemyStatsChart,
  'shop-pricing': ShopPricingChart,
  'progression': ProgressionChart,
  'config': FormulaEditor,
};

export default function App() {
  const [activePanel, setActivePanel] = useState('weapon-sweep');
  const PanelComponent = PANELS[activePanel];

  return (
    <QueryClientProvider client={queryClient}>
      <Layout activePanel={activePanel} onNavigate={setActivePanel}>
        {PanelComponent ? <PanelComponent /> : <div className="text-zinc-400">Select a panel</div>}
      </Layout>
    </QueryClientProvider>
  );
}
