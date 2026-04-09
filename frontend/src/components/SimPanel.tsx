import type { ReactNode } from 'react';

interface Props {
  title: string;
  subtitle?: string;
  controls?: ReactNode;
  children: ReactNode;
  isLoading?: boolean;
  error?: string | null;
}

export default function SimPanel({ title, subtitle, controls, children, isLoading, error }: Props) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h2 className="text-xl font-bold text-zinc-100">{title}</h2>
        {subtitle && <p className="text-sm text-zinc-400 mt-1">{subtitle}</p>}
      </div>

      {controls && (
        <div className="flex flex-wrap items-end gap-4 bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
          {controls}
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded p-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 bg-zinc-900/50 flex items-center justify-center z-10 rounded">
            <div className="text-zinc-400 text-sm">Loading...</div>
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
