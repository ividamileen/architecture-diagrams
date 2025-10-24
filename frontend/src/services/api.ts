import axios from 'axios';
import type { Message, Conversation, Diagram, ModificationRequest, ModificationResponse } from '../types';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Conversations
export const conversationsApi = {
  create: async (data: { platform: 'web' | 'teams' }) => {
    const response = await api.post<Conversation>('/conversations/', data);
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<Conversation>(`/conversations/${id}`);
    return response.data;
  },
};

// Messages
export const messagesApi = {
  create: async (data: {
    content: string;
    user_id: string;
    user_name?: string;
    conversation_id?: number;
    platform?: 'web' | 'teams';
  }) => {
    const response = await api.post<Message>('/messages/', {
      ...data,
      platform: data.platform || 'web',
    });
    return response.data;
  },

  getByConversation: async (conversationId: number, limit: number = 50) => {
    const response = await api.get<Message[]>(`/messages/conversation/${conversationId}`, {
      params: { limit },
    });
    return response.data;
  },

  getTechnical: async (conversationId: number, timeWindowMinutes?: number) => {
    const response = await api.get<Message[]>(`/messages/conversation/${conversationId}/technical`, {
      params: { time_window_minutes: timeWindowMinutes },
    });
    return response.data;
  },
};

// Diagrams
export const diagramsApi = {
  generate: async (data: { conversation_id: number; force_regenerate?: boolean }) => {
    const response = await api.post<Diagram>('/diagrams/generate', data);
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<Diagram>(`/diagrams/${id}`);
    return response.data;
  },

  getByConversation: async (conversationId: number) => {
    const response = await api.get<Diagram[]>(`/diagrams/conversation/${conversationId}`);
    return response.data;
  },

  modify: async (data: ModificationRequest) => {
    const response = await api.post<ModificationResponse>('/diagrams/modify', data);
    return response.data;
  },

  updateCode: async (diagramId: number, plantumlCode?: string, drawioXml?: string) => {
    const response = await api.put<Diagram>(`/diagrams/${diagramId}/code`, {
      plantuml_code: plantumlCode,
      drawio_xml: drawioXml,
    });
    return response.data;
  },

  getPng: (diagramId: number) => {
    return `${API_BASE_URL}/diagrams/${diagramId}/png`;
  },

  getPlantUml: async (diagramId: number) => {
    const response = await api.get<{ diagram_id: number; code: string }>(`/diagrams/${diagramId}/plantuml`);
    return response.data;
  },

  getDrawio: async (diagramId: number) => {
    const response = await api.get<{ diagram_id: number; xml: string }>(`/diagrams/${diagramId}/drawio`);
    return response.data;
  },
};

export default api;
