/**
 * Analytics API service.
 */

import apiClient from './api';
import type {
  OrderAnalyticsResponse,
  CampaignAnalyticsResponse,
  ConsumerAnalyticsResponse,
  FeedbackAnalyticsResponse,
  InsightResponse,
} from '../types/analytics';

export const analyticsService = {
  /**
   * Get order analytics.
   */
  async getOrders(startDate?: string, endDate?: string): Promise<OrderAnalyticsResponse> {
    const params: Record<string, string> = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    
    const response = await apiClient.get('/analytics/orders', { params });
    return response.data;
  },

  /**
   * Get campaign analytics.
   */
  async getCampaigns(): Promise<CampaignAnalyticsResponse> {
    const response = await apiClient.get('/analytics/campaigns');
    return response.data;
  },

  /**
   * Get consumer analytics.
   */
  async getConsumers(): Promise<ConsumerAnalyticsResponse> {
    const response = await apiClient.get('/analytics/consumers');
    return response.data;
  },

  /**
   * Get feedback analytics.
   */
  async getFeedbacks(): Promise<FeedbackAnalyticsResponse> {
    const response = await apiClient.get('/analytics/feedbacks');
    return response.data;
  },

  /**
   * Get AI-generated insights for a dashboard page.
   */
  async getInsights(pageType: string): Promise<InsightResponse> {
    const response = await apiClient.post('/analytics/insights', {
      page_type: pageType,
    });
    return response.data;
  },
};

