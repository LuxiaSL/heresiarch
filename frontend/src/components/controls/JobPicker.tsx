import { useJobs } from '../../hooks/useGameData';

interface Props {
  value: string;
  onChange: (v: string) => void;
  label?: string;
}

export default function JobPicker({ value, onChange, label = 'Job' }: Props) {
  const { data: jobs } = useJobs();
  if (!jobs) return null;
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-zinc-400">{label}</span>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="bg-zinc-800 border border-zinc-600 rounded px-2 py-1 text-zinc-100"
      >
        {Object.values(jobs).map(j => (
          <option key={j.id} value={j.id}>{j.name} ({j.origin})</option>
        ))}
      </select>
    </label>
  );
}
