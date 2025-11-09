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
        setError('Failed to load order analytics');
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
        <div className="loading">Loading order analytics...</div>
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
        Orders Dashboard
      </h1>

      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Total Orders</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            {data.total_orders.toLocaleString()}
          </p>
        </div>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Total Revenue</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            R$ {(data.total_revenue / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Average Order Value</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            R$ {(data.average_order_value / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="card">
        <h3 className="card-title">Orders Over Time</h3>
        <OrdersChart data={data.daily_data} />
      </div>

      {/* AI Insights */}
      <InsightsCard pageType="orders" />
    </div>
  );
}

