import { useState, type ReactNode } from 'react';

interface NavItem {
  id: string;
  label: string;
  group: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'weapon-sweep', label: 'Weapon Sweep', group: 'Weapon Scaling' },
  { id: 'converter', label: 'Converters', group: 'Weapon Scaling' },
  { id: 'sigmoid', label: 'Sigmoid Explorer', group: 'Weapon Scaling' },
  { id: 'ability-dpr', label: 'Ability DPR', group: 'Ability Balance' },
  { id: 'ability-compare', label: 'Ability Compare', group: 'Ability Balance' },
  { id: 'job-curve', label: 'Job Curve', group: 'Ability Balance' },
  { id: 'build-compare', label: 'Build Compare', group: 'Build Analysis' },
  { id: 'economy', label: 'Economy', group: 'Economy & XP' },
  { id: 'xp-curve', label: 'XP Curve', group: 'Economy & XP' },
  { id: 'shop-pricing', label: 'Shop Pricing', group: 'Economy & XP' },
  { id: 'enemy-stats', label: 'Enemy Stats', group: 'Enemies' },
  { id: 'progression', label: 'Full Progression', group: 'Full Run' },
  { id: 'config', label: 'Formula Config', group: 'Settings' },
];

const GROUPS = [...new Set(NAV_ITEMS.map(n => n.group))];

interface Props {
  activePanel: string;
  onNavigate: (panel: string) => void;
  children: ReactNode;
}

export default function Layout({ activePanel, onNavigate, children }: Props) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-zinc-900 text-zinc-100">
      {/* Sidebar */}
      <nav className={`${collapsed ? 'w-12' : 'w-56'} flex-shrink-0 bg-zinc-950 border-r border-zinc-800 flex flex-col transition-all duration-200`}>
        <div className="p-3 border-b border-zinc-800 flex items-center justify-between">
          {!collapsed && <span className="font-bold text-sm tracking-wide">HERESIARCH</span>}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="text-zinc-400 hover:text-zinc-100 text-xs"
            title={collapsed ? 'Expand' : 'Collapse'}
          >
            {collapsed ? '>' : '<'}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {!collapsed && GROUPS.map(group => (
            <div key={group} className="mb-2">
              <div className="px-3 py-1 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                {group}
              </div>
              {NAV_ITEMS.filter(n => n.group === group).map(item => (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`w-full text-left px-3 py-1.5 text-sm transition-colors ${
                    activePanel === item.id
                      ? 'bg-blue-600/20 text-blue-400 border-r-2 border-blue-400'
                      : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          ))}
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-6">
        {children}
      </main>
    </div>
  );
}
