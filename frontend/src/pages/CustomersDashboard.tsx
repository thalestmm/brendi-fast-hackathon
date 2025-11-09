/**
 * Customers Dashboard page.
 */

import { useEffect, useState } from 'react';
import { analyticsService } from '../services/analytics';
import { InsightsCard } from '../components/InsightsCard';
import type { ConsumerAnalyticsResponse } from '../types/analytics';

export function CustomersDashboard() {
  const [data, setData] = useState<ConsumerAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const analytics = await analyticsService.getConsumers();
        setData(analytics);
      } catch (err) {
        setError('Failed to load consumer analytics');
        console.error('Error fetching consumers:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="container" style={{ paddingTop: '40px' }}>
        <div className="loading">Loading consumer analytics...</div>
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
        Customers Dashboard
      </h1>

      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Total Customers</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            {data.total_consumers.toLocaleString()}
          </p>
        </div>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Avg Orders per Customer</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            {data.average_orders_per_consumer.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Top Customers */}
      <div className="card">
        <h3 className="card-title">Top Customers</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {data.top_customers.map((customer, index) => (
            <div key={customer.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '6px' }}>
              <div>
                <span style={{ fontWeight: '600', marginRight: '8px' }}>#{index + 1}</span>
                <span>{customer.name || 'Unknown'}</span>
                {customer.phone && <span style={{ color: '#666', marginLeft: '8px' }}>({customer.phone})</span>}
              </div>
              <span style={{ fontWeight: '600', color: 'var(--primary-red)' }}>
                {customer.order_count || 0} orders
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insights */}
      <InsightsCard pageType="consumers" />
    </div>
  );
}

