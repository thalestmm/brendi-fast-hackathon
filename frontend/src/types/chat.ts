/**
 * Chat types.
 */

export interface ChatMessageRequest {
  message: string;
  session_id?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ChatMessageResponse {
  message: ChatMessage;
  session_id: string;
}

export interface ChatSession {
  id: string;
  store_id: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count?: number;
}

export interface ChatSessionsResponse {
  sessions: ChatSession[];
  total: number;
}

