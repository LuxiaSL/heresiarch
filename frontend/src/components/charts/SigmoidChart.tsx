import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';
import { useSimQuery } from '../../hooks/useSimQuery';
import { simSigmoid } from '../../api/client';
import type { SigmoidResult } from '../../api/types';
import SimPanel from '../SimPanel';
import NumberInput from '../controls/NumberInput';

export default function SigmoidChart() {
  const [maxOutput, setMaxOutput] = useState(200);
  const [midpoint, setMidpoint] = useState(300);
  const [rate, setRate] = useState(0.015);

  const params = { max_output: maxOutput, midpoint, rate };
  const { data, isLoading, error } = useSimQuery<SigmoidResult>('sigmoid', simSigmoid, params);

  const chartData = data?.points.map(p => ({
    stat: p.stat,
    output: p.output,
    pct: p.pct_of_max,
  })) ?? [];

  return (
    <SimPanel
      title="Sigmoid Scaling Curve"
      subtitle={data ? `max=${data.max_output}, midpoint=${data.midpoint}, rate=${data.rate}` : undefined}
      isLoading={isLoading}
      error={error?.message}
      controls={<>
        <NumberInput value={maxOutput} onChange={setMaxOutput} label="Max Output" min={1} max={9999} />
        <NumberInput value={midpoint} onChange={setMidpoint} label="Midpoint" min={1} max={9999} />
        <NumberInput value={rate} onChange={setRate} label="Rate" min={0.001} max={1} step={0.001} />
      </>}
    >
      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="stat"
              stroke="#9ca3af"
              label={{ value: 'Stat Value', position: 'bottom', fill: '#9ca3af' }}
            />
            <YAxis
              stroke="#9ca3af"
              label={{ value: 'Output', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
            />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: '1px solid #4b5563', borderRadius: '8px' }}
              labelStyle={{ color: '#e5e7eb' }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(value: any) => [Number(value).toFixed(1)]}
            />
            <Legend />
            <ReferenceLine
              y={maxOutput}
              stroke="#f97316"
              strokeDasharray="6 4"
              label={{ value: `Max: ${maxOutput}`, fill: '#f97316', position: 'right', fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="output"
              stroke="#60a5fa"
              strokeWidth={2}
              dot={false}
              name="Output"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </SimPanel>
  );
}
