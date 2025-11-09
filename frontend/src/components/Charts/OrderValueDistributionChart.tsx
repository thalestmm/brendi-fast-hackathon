/**
 * Order value distribution chart.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { OrderValueBucket } from '../../types/analytics';

interface OrderValueDistributionChartProps {
  data: OrderValueBucket[];
}

export function OrderValueDistributionChart({ data }: OrderValueDistributionChartProps) {
  const chartData = data.map((item) => ({
    ...item,
    revenue: item.revenue / 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="bucket" />
        <YAxis />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === 'revenue') {
              return [`R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, 'Receita'];
            }
            return [value, 'Pedidos'];
          }}
        />
        <Bar dataKey="orders" name="Pedidos" fill="var(--primary-red)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}


