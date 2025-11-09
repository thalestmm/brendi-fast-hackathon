/**
 * Orders by day of week chart.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { DayOfWeekData } from '../../types/analytics';

interface OrdersByDayOfWeekChartProps {
  data: DayOfWeekData[];
}

const dayOrder = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];

export function OrdersByDayOfWeekChart({ data }: OrdersByDayOfWeekChartProps) {
  const chartData = [...data]
    .map((item) => ({
      ...item,
      revenue: item.revenue / 100,
    }))
    .sort((a, b) => {
      const indexA = dayOrder.indexOf(a.day);
      const indexB = dayOrder.indexOf(b.day);
      return (indexA === -1 ? 7 : indexA) - (indexB === -1 ? 7 : indexB);
    });

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="day" />
        <YAxis yAxisId="left" />
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
        <Bar yAxisId="left" dataKey="orders" name="Pedidos" fill="var(--primary-red)" radius={[4, 4, 0, 0]} />
        <Bar
          yAxisId="right"
          dataKey="revenue"
          name="Receita (R$)"
          fill="#666"
          radius={[4, 4, 0, 0]}
          opacity={0.65}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}


