import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchFormulas, updateFormulas, saveFormulas, resetFormulas } from '../../api/client';
import type { FormulaConfig } from '../../api/types';

const FORMULA_FIELDS: Array<{ key: keyof FormulaConfig; label: string; min: number; max: number; step: number }> = [
  { key: 'HP_COEFFICIENT', label: 'HP Coefficient', min: 0, max: 5, step: 0.1 },
  { key: 'DEF_REDUCTION_RATIO', label: 'DEF Reduction Ratio', min: 0, max: 1, step: 0.05 },
  { key: 'RES_THRESHOLD_RATIO', label: 'RES Threshold Ratio', min: 0, max: 1, step: 0.05 },
  { key: 'SPD_THRESHOLD', label: 'SPD Threshold', min: 10, max: 500, step: 10 },
  { key: 'SURVIVE_DAMAGE_REDUCTION', label: 'Survive Damage Reduction', min: 0, max: 1, step: 0.05 },
  { key: 'PARTIAL_ACTION_DAMAGE_RATIO', label: 'Partial Action Damage', min: 0, max: 1, step: 0.05 },
  { key: 'MAX_ACTION_POINT_BANK', label: 'Max Action Point Bank', min: 1, max: 10, step: 1 },
  { key: 'XP_THRESHOLD_BASE', label: 'XP Threshold Base', min: 1, max: 50, step: 1 },
  { key: 'XP_THRESHOLD_EXPONENT', label: 'XP Threshold Exponent', min: 1, max: 4, step: 0.1 },
  { key: 'XP_OVERLEVEL_PENALTY_PER_LEVEL', label: 'XP Overlevel Penalty/Lv', min: 0, max: 1, step: 0.05 },
  { key: 'XP_MINIMUM_RATIO', label: 'XP Minimum Ratio', min: 0, max: 1, step: 0.05 },
  { key: 'CHA_PRICE_MODIFIER_PER_POINT', label: 'CHA Price Modifier/Point', min: 0, max: 0.05, step: 0.001 },
  { key: 'SELL_RATIO', label: 'Sell Ratio', min: 0, max: 1, step: 0.05 },
  { key: 'MONEY_DROP_MIN_MULTIPLIER', label: 'Money Drop Min Mult', min: 1, max: 20, step: 1 },
  { key: 'MONEY_DROP_MAX_MULTIPLIER', label: 'Money Drop Max Mult', min: 5, max: 50, step: 1 },
  { key: 'OVERSTAY_PENALTY_PER_BATTLE', label: 'Overstay Penalty/Battle', min: 0, max: 0.2, step: 0.005 },
];

export default function FormulaEditor() {
  const queryClient = useQueryClient();
  const { data: config } = useQuery({ queryKey: ['formulas'], queryFn: fetchFormulas });
  const [local, setLocal] = useState<FormulaConfig | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (config && !local) setLocal(config);
  }, [config, local]);

  const updateMut = useMutation({
    mutationFn: updateFormulas,
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });

  const saveMut = useMutation({
    mutationFn: saveFormulas,
    onSuccess: () => setSaved(true),
  });

  const resetMut = useMutation({
    mutationFn: resetFormulas,
    onSuccess: (data) => {
      setLocal(data);
      queryClient.invalidateQueries();
    },
  });

  if (!local) return null;

  const handleChange = (key: keyof FormulaConfig, value: number) => {
    const updated = { ...local, [key]: value };
    setLocal(updated);
    setSaved(false);
    updateMut.mutate(updated);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-zinc-100">Formula Constants</h2>
        <div className="flex gap-2">
          <button
            onClick={() => saveMut.mutate()}
            className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white text-sm rounded transition-colors"
          >
            {saved ? 'Saved!' : 'Save to Disk'}
          </button>
          <button
            onClick={() => resetMut.mutate()}
            className="px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 text-white text-sm rounded transition-colors"
          >
            Reset Defaults
          </button>
        </div>
      </div>
      <p className="text-sm text-zinc-400">
        Adjust formula constants below. Changes apply to all simulations in real-time.
        Click "Save to Disk" to persist.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {FORMULA_FIELDS.map(({ key, label, min, max, step }) => (
          <div key={key} className="bg-zinc-800/50 rounded p-3 border border-zinc-700">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-zinc-300">{label}</span>
              <span className="text-zinc-100 font-mono">{local[key]}</span>
            </div>
            <input
              type="range"
              min={min}
              max={max}
              step={step}
              value={local[key]}
              onChange={e => handleChange(key, Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <div className="flex justify-between text-xs text-zinc-500 mt-0.5">
              <span>{min}</span>
              <span>{max}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
