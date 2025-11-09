/**
 * Top menu items chart.
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts';
import type { TopMenuItem } from '../../types/analytics';

interface TopMenuItemsChartProps {
  data: TopMenuItem[];
}

export function TopMenuItemsChart({ data }: TopMenuItemsChartProps) {
  const chartData = [...data]
    .map((item) => ({
      ...item,
      revenue: item.revenue / 100,
    }))
    .sort((a, b) => b.revenue - a.revenue);

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis type="category" dataKey="name" width={220} />
        <Tooltip
          formatter={(value: number) => {
            return [`R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, 'Receita'];
          }}
          labelFormatter={(label, payload) => {
            const item = payload?.[0]?.payload;
            return `${label} — ${item?.orders ?? 0} pedidos`;
          }}
        />
        <Bar dataKey="revenue" name="Receita (R$)" fill="var(--primary-red)" radius={[0, 6, 6, 0]}>
          <LabelList
            dataKey="orders"
            position="insideRight"
            formatter={(value: number) => `${value} pedidos`}
            fill="#fff"
            style={{ fontSize: 12 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}


