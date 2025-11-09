/**
 * Orders chart component using Recharts.
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { DailyData } from '../../types/analytics';

interface OrdersChartProps {
  data: DailyData[];
}

export function OrdersChart({ data }: OrdersChartProps) {
  // Format data for chart
  const chartData = data
    .map((item) => ({
      rawDate: item.date,
      date: item.date ? new Date(item.date).toLocaleDateString('pt-BR', { month: 'short', day: 'numeric' }) : '',
      orders: item.orders,
      revenue: item.revenue / 100, // Convert from cents to reais
    }))
    .sort((a, b) => {
      if (!a.rawDate || !b.rawDate) return 0;
      return new Date(a.rawDate).getTime() - new Date(b.rawDate).getTime();
    });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis yAxisId="left" label={{ value: 'Pedidos', angle: -90, position: 'insideLeft' }} />
        <YAxis
          yAxisId="right"
          orientation="right"
          label={{ value: 'Receita (R$)', angle: 90, position: 'insideRight' }}
        />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === 'revenue') {
              return [`R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, 'Receita'];
            }
            return [value, 'Pedidos'];
          }}
          labelFormatter={(label) => `Dia ${label}`}
        />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="orders"
          stroke="var(--primary-red)"
          strokeWidth={2}
          name="Pedidos"
          activeDot={{ r: 6 }}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="revenue"
          stroke="#666"
          strokeWidth={2}
          name="Receita"
          strokeDasharray="4 4"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

