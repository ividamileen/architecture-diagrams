import type { WebSocketMessage } from '../types';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private conversationId: number | null = null;
  private listeners: ((message: WebSocketMessage) => void)[] = [];

  connect(conversationId: number) {
    this.conversationId = conversationId;
    const wsUrl = `ws://localhost:8000/api/v1/messages/ws/${conversationId}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.notifyListeners(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (this.conversationId) {
          this.connect(this.conversationId);
        }
      }, 3000);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.conversationId = null;
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  subscribe(listener: (message: WebSocketMessage) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notifyListeners(message: WebSocketMessage) {
    this.listeners.forEach((listener) => listener(message));
  }
}

export const wsService = new WebSocketService();
