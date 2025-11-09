/**
 * API client for backend communication.
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';

// Use relative URL in production (nginx proxies /api to backend)
// Use absolute URL in development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? '' : 'http://localhost:8000');
const DEFAULT_STORE_ID = import.meta.env.VITE_DEFAULT_STORE_ID || '0WcZ1MWEaFc1VftEBdLa';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
    'X-Store-ID': DEFAULT_STORE_ID,
  },
});

// Request interceptor to add store_id header
apiClient.interceptors.request.use((config) => {
  const storeId = localStorage.getItem('store_id') || DEFAULT_STORE_ID;
  if (config.headers) {
    config.headers['X-Store-ID'] = storeId;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;

