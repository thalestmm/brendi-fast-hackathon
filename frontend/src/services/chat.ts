/**
 * Chat API service.
 */

import apiClient from './api';
import type {
  ChatMessageRequest,
  ChatMessageResponse,
  ChatSessionsResponse,
} from '../types/chat';

export const chatService = {
  /**
   * Send a message to the AI agent.
   */
  async sendMessage(
    message: string,
    sessionId?: string
  ): Promise<ChatMessageResponse> {
    const response = await apiClient.post<ChatMessageResponse>('/chat/message', {
      message,
      session_id: sessionId,
    } as ChatMessageRequest);
    return response.data;
  },

  /**
   * Get chat sessions for the current store.
   */
  async getSessions(limit = 20, offset = 0): Promise<ChatSessionsResponse> {
    const response = await apiClient.get<ChatSessionsResponse>('/chat/sessions', {
      params: { limit, offset },
    });
    return response.data;
  },
};

