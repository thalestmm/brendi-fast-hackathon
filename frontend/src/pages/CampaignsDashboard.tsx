/**
 * Campaigns Dashboard page.
 */

import { useEffect, useState } from 'react';
import { analyticsService } from '../services/analytics';
import { InsightsCard } from '../components/InsightsCard';
import type { CampaignAnalyticsResponse } from '../types/analytics';

export function CampaignsDashboard() {
  const [data, setData] = useState<CampaignAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const analytics = await analyticsService.getCampaigns();
        setData(analytics);
      } catch (err) {
        setError('Failed to load campaign analytics');
        console.error('Error fetching campaigns:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="container" style={{ paddingTop: '40px' }}>
        <div className="loading">Loading campaign analytics...</div>
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
        Campaigns Dashboard
      </h1>

      {/* Key Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Total Campaigns</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            {data.total_campaigns.toLocaleString()}
          </p>
        </div>
        <div className="card">
          <h3 style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Avg Conversion Rate</h3>
          <p style={{ fontSize: '32px', fontWeight: '600', color: 'var(--primary-red)' }}>
            {data.average_conversion_rate.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Campaigns by Status */}
      <div className="card">
        <h3 className="card-title">Campaigns by Status</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {Object.entries(data.campaigns_by_status).map(([status, count]) => (
            <div key={status} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ textTransform: 'capitalize' }}>{status || 'Unknown'}</span>
              <span style={{ fontWeight: '600' }}>{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Campaigns by Type */}
      <div className="card">
        <h3 className="card-title">Campaigns by Type</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {Object.entries(data.campaigns_by_type).map(([type, count]) => (
            <div key={type} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ textTransform: 'capitalize' }}>{type || 'Unknown'}</span>
              <span style={{ fontWeight: '600' }}>{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insights */}
      <InsightsCard pageType="campaigns" />
    </div>
  );
}

