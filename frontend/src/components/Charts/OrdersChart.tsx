/**
 * Orders chart component using Recharts.
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { DailyData } from '../../types/analytics';

interface OrdersChartProps {
  data: DailyData[];
}

export function OrdersChart({ data }: OrdersChartProps) {
  // Format data for chart
  const chartData = data.map((item) => ({
    date: item.date ? new Date(item.date).toLocaleDateString('pt-BR', { month: 'short', day: 'numeric' }) : '',
    orders: item.orders,
    revenue: item.revenue / 100, // Convert from cents to reais
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === 'revenue') {
              return [`R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, 'Revenue'];
            }
            return [value, 'Orders'];
          }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="orders"
          stroke="var(--primary-red)"
          strokeWidth={2}
          name="Orders"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="revenue"
          stroke="#666"
          strokeWidth={2}
          name="Revenue"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

