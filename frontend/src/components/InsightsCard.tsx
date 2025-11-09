/**
 * Insights card component for displaying AI-generated insights.
 */

import { useEffect, useState } from 'react';
import { analyticsService } from '../services/analytics';
import type { InsightResponse } from '../types/analytics';

interface InsightsCardProps {
  pageType: string;
}

export function InsightsCard({ pageType }: InsightsCardProps) {
  const [insight, setInsight] = useState<InsightResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchInsight() {
      try {
        setLoading(true);
        setError(null);
        const data = await analyticsService.getInsights(pageType);
        setInsight(data);
      } catch (err) {
        setError('Falha ao carregar insights');
        console.error('Error fetching insights:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchInsight();
  }, [pageType]);

  if (loading) {
    return (
      <div className="card">
        <h3 className="card-title">Insights da IA</h3>
        <div className="loading">Carregando insights...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h3 className="card-title">Insights da IA</h3>
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="card-title">Insights da IA</h3>
      <p style={{ lineHeight: '1.6', color: '#666' }}>{insight?.insight}</p>
      {insight?.generated_at && (
        <p style={{ fontSize: '12px', color: '#999', marginTop: '12px' }}>
          Gerado em {new Date(insight.generated_at).toLocaleString('pt-BR')}
        </p>
      )}
    </div>
  );
}

