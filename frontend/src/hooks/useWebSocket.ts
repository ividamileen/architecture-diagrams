import { useEffect, useState } from 'react';
import { wsService } from '../services/websocket';
import type { WebSocketMessage } from '../types';

export function useWebSocket(conversationId: number | null) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    if (!conversationId) return;

    // Connect to WebSocket
    wsService.connect(conversationId);
    setIsConnected(true);

    // Subscribe to messages
    const unsubscribe = wsService.subscribe((message) => {
      setLastMessage(message);
    });

    // Cleanup
    return () => {
      unsubscribe();
      wsService.disconnect();
      setIsConnected(false);
    };
  }, [conversationId]);

  const sendMessage = (data: any) => {
    wsService.send(data);
  };

  return {
    isConnected,
    lastMessage,
    sendMessage,
  };
}
