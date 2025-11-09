/**
 * Orders by hour of day chart.
 */

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Line } from 'recharts';
import type { HourlyData } from '../../types/analytics';

interface OrdersByHourChartProps {
  data: HourlyData[];
}

export function OrdersByHourChart({ data }: OrdersByHourChartProps) {
  const chartData = [...data]
    .map((item) => ({
      ...item,
      revenue: item.revenue / 100,
    }))
    .sort((a, b) => a.hour - b.hour)
    .map((item) => ({
      ...item,
      label: `${item.hour.toString().padStart(2, '0')}h`,
    }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis yAxisId="left" label={{ value: 'Pedidos', angle: -90, position: 'insideLeft' }} />
        <YAxis yAxisId="right" orientation="right" hide />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === 'revenue') {
              return [`R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, 'Receita'];
            }
            return [value, 'Pedidos'];
          }}
        />
        <Legend />
        <Area
          yAxisId="left"
          type="monotone"
          dataKey="orders"
          name="Pedidos"
          stroke="var(--primary-red)"
          fill="var(--primary-red)"
          fillOpacity={0.2}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="revenue"
          name="Receita (R$)"
          stroke="#666"
          strokeWidth={2}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}


