/**
 * Orders Dashboard page.
 */

import { useEffect, useState } from 'react';
import { analyticsService } from '../services/analytics';
import { InsightsCard } from '../components/InsightsCard';
import {
  OrdersByDayOfWeekChart,
  OrderValueDistributionChart,
  TopMenuItemsChart,
  OrdersByStatusChart,
  TopDeliveryAreasChart,
} from '../components/Charts';
import type { OrderAnalyticsResponse } from '../types/analytics';

export function OrdersDashboard() {
  const [data, setData] = useState<OrderAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const analytics = await analyticsService.getOrders();
        setData({
          ...analytics,
          total_orders: analytics.total_orders ?? 0,
          total_revenue: analytics.total_revenue ?? 0,
          average_order_value: analytics.average_order_value ?? 0,
          daily_data: analytics.daily_data ?? [],
          orders_by_day_of_week: analytics.orders_by_day_of_week ?? [],
          orders_by_hour: analytics.orders_by_hour ?? [],
          order_value_distribution: analytics.order_value_distribution ?? [],
          top_menu_items: analytics.top_menu_items ?? [],
          orders_by_status: analytics.orders_by_status ?? [],
          top_delivery_areas: analytics.top_delivery_areas ?? [],
          period: analytics.period ?? { start: null, end: null },
        });
      } catch (err) {
        setError('Falha ao carregar analytics de pedidos');
        console.error('Error fetching orders:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="container" style={{ paddingTop: '40px' }}>
        <div className="loading">Carregando analytics de pedidos...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container" style={{ paddingTop: '40px' }}>
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="container" style={{ paddingTop: '40px', paddingBottom: '100px' }}>
      <h1 style={{ marginBottom: '32px', fontSize: '32px', fontWeight: '600' }}>
        Dashboard de Pedidos
      </h1>

      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Total de Pedidos</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            {data.total_orders.toLocaleString('pt-BR')}
          </p>
        </div>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Receita Total</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            R$ {(data.total_revenue / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Ticket Médio</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            R$ {(data.average_order_value / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '24px',
          marginTop: '24px',
          alignItems: 'stretch',
        }}
      >
        <div className="card">
          <h3 className="card-title">Pedidos por Dia da Semana</h3>
          {data.orders_by_day_of_week.length > 0 ? (
            <OrdersByDayOfWeekChart data={data.orders_by_day_of_week} />
          ) : (
            <div style={{ padding: '16px', color: '#777', fontSize: '14px' }}>Sem dados suficientes.</div>
          )}
        </div>

        <div className="card">
          <h3 className="card-title">Ticket Médio por Faixa de Valor</h3>
          {data.order_value_distribution.length > 0 ? (
            <OrderValueDistributionChart data={data.order_value_distribution} />
          ) : (
            <div style={{ padding: '16px', color: '#777', fontSize: '14px' }}>Sem dados suficientes.</div>
          )}
        </div>

        <div className="card">
          <h3 className="card-title">Itens mais Vendidos</h3>
          {data.top_menu_items.length > 0 ? (
            <TopMenuItemsChart data={data.top_menu_items} />
          ) : (
            <div style={{ padding: '16px', color: '#777', fontSize: '14px' }}>Sem dados suficientes.</div>
          )}
        </div>

        <div className="card" style={{ gridColumn: 'span 2' }}>
          <h3 className="card-title">Pedidos por Status</h3>
          {data.orders_by_status.length > 0 ? (
            <OrdersByStatusChart data={data.orders_by_status} />
          ) : (
            <div style={{ padding: '16px', color: '#777', fontSize: '14px' }}>Sem dados suficientes.</div>
          )}
        </div>

        <div className="card" style={{ gridColumn: 'span 2' }}>
          <h3 className="card-title">Bairros com Mais Pedidos</h3>
          {data.top_delivery_areas.length > 0 ? (
            <TopDeliveryAreasChart data={data.top_delivery_areas} />
          ) : (
            <div style={{ padding: '16px', color: '#777', fontSize: '14px' }}>Sem dados suficientes.</div>
          )}
        </div>
      </div>

      {/* AI Insights */}
      <InsightsCard pageType="orders" />
    </div>
  );
}

