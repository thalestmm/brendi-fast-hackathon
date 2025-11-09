/**
 * Top delivery areas chart.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts';
import type { ReactNode } from 'react';
import type { DeliveryAreaBreakdown } from '../../types/analytics';

interface TopDeliveryAreasChartProps {
  data: DeliveryAreaBreakdown[];
}

export function TopDeliveryAreasChart({ data }: TopDeliveryAreasChartProps) {
  const chartData = [...data]
    .map((item) => ({
      ...item,
      revenue: item.revenue / 100,
    }))
    .sort((a, b) => b.orders - a.orders);

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis type="category" dataKey="area" width={220} />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === 'orders') {
              return [`${value} pedidos`, 'Pedidos'];
            }
            return [`R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, 'Receita'];
          }}
        />
        <Bar dataKey="orders" name="Pedidos" fill="var(--primary-red)" radius={[0, 6, 6, 0]}>
          <LabelList
            dataKey="revenue"
            position="right"
            formatter={(label: ReactNode) =>
              typeof label === 'number'
                ? `R$ ${label.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                : label ?? ''
            }
            style={{ fontSize: 12, fill: '#444' }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}


