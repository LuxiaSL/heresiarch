interface Props {
  value: number;
  onChange: (v: number) => void;
  label: string;
  min?: number;
  max?: number;
  step?: number;
}

export default function NumberInput({ value, onChange, label, min, max, step = 1 }: Props) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-zinc-400">{label}</span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={e => onChange(Number(e.target.value))}
        className="bg-zinc-800 border border-zinc-600 rounded px-2 py-1 text-zinc-100 w-24"
      />
    </label>
  );
}
