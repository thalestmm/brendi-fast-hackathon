/**
 * Orders by status chart.
 */

import { PieChart, Pie, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import type { OrderStatusBreakdown } from '../../types/analytics';

interface OrdersByStatusChartProps {
  data: OrderStatusBreakdown[];
}

const COLORS = ['#db4542', '#111827', '#9CA3AF', '#F59E0B', '#2563EB', '#10B981', '#7C3AED'];

export function OrdersByStatusChart({ data }: OrdersByStatusChartProps) {
  const chartData = data.map((item) => ({
    ...item,
    revenue: item.revenue / 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="orders"
          nameKey="status"
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={90}
          paddingAngle={4}
        >
          {chartData.map((entry, index) => (
            <Cell key={entry.status} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number, name: string, props) => {
            const revenue = (props.payload as (typeof chartData)[number]).revenue;
            return [
              `${value} pedidos · R$ ${revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
              name,
            ];
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}


