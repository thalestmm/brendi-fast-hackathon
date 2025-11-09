/**
 * Analytics types.
 */

export interface DailyData {
  date: string | null;
  orders: number;
  revenue: number;
}

export interface OrderAnalyticsResponse {
  total_orders: number;
  total_revenue: number;
  average_order_value: number;
  daily_data: DailyData[];
  period: {
    start: string | null;
    end: string | null;
  };
}

export interface CampaignAnalyticsResponse {
  total_campaigns: number;
  campaigns_by_status: Record<string, number>;
  campaigns_by_type: Record<string, number>;
  average_conversion_rate: number;
}

export interface TopCustomer {
  id: string;
  name: string | null;
  phone: string | null;
  order_count: number | null;
}

export interface ConsumerAnalyticsResponse {
  total_consumers: number;
  average_orders_per_consumer: number;
  top_customers: TopCustomer[];
}

export interface CategoryFeedback {
  count: number;
  average_rating: number;
}

export interface FeedbackAnalyticsResponse {
  total_feedbacks: number;
  average_rating: number;
  feedbacks_by_category: Record<string, CategoryFeedback>;
}

export interface InsightRequest {
  page_type: string;
  context?: Record<string, unknown>;
}

export interface InsightResponse {
  insight: string;
  page_type: string;
  generated_at: string;
}

