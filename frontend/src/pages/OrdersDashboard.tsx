/**
 * Orders Dashboard page.
 */

import { useEffect, useState } from 'react';
import { analyticsService } from '../services/analytics';
import { InsightsCard } from '../components/InsightsCard';
import { OrdersChart } from '../components/Charts/OrdersChart';
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
        setData(analytics);
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

      {/* Chart */}
      <div className="card">
        <h3 className="card-title">Pedidos ao Longo do Tempo</h3>
        <OrdersChart data={data.daily_data} />
      </div>

      {/* AI Insights */}
      <InsightsCard pageType="orders" />
    </div>
  );
}

