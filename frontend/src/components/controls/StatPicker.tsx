const STATS = ['STR', 'MAG', 'DEF', 'RES', 'SPD'];

interface Props {
  value: string;
  onChange: (v: string) => void;
  label?: string;
}

export default function StatPicker({ value, onChange, label = 'Stat' }: Props) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-zinc-400">{label}</span>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="bg-zinc-800 border border-zinc-600 rounded px-2 py-1 text-zinc-100"
      >
        {STATS.map(s => <option key={s} value={s}>{s}</option>)}
      </select>
    </label>
  );
}
