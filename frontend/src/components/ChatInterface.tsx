import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { messagesApi } from '../services/api';
import type { Message } from '../types';
import { clsx } from 'clsx';

interface ChatInterfaceProps {
  conversationId: number;
  messages: Message[];
  onMessageSent: (message: Message) => void;
  onDiagramGenerationStarted: () => void;
}

export function ChatInterface({
  conversationId,
  messages,
  onMessageSent,
  onDiagramGenerationStarted,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    setSending(true);
    try {
      const message = await messagesApi.create({
        content: input.trim(),
        user_id: 'user-1',
        user_name: 'User',
        conversation_id: conversationId,
        platform: 'web',
      });

      onMessageSent(message);
      setInput('');

      // Check if diagram generation should be triggered
      if (message.is_technical && message.confidence_score >= 0.7) {
        // In production, this would be handled by the backend
        // For now, we notify the parent component
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className="space-y-1">
            <div className="flex items-start space-x-3">
              {/* Avatar */}
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center text-white text-sm font-medium">
                  {message.user_name?.[0] || 'U'}
                </div>
              </div>

              {/* Message content */}
              <div className="flex-1 space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-gray-900">
                    {message.user_name || message.user_id}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                  {message.is_technical && (
                    <span
                      className={clsx(
                        'text-xs px-2 py-0.5 rounded-full',
                        message.confidence_score >= 0.7
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      )}
                    >
                      Technical ({(message.confidence_score * 100).toFixed(0)}%)
                    </span>
                  )}
                </div>
                <div className="text-gray-700 whitespace-pre-wrap">{message.content}</div>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (technical discussions will trigger diagram generation)"
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            rows={3}
            disabled={sending}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {sending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Tip: Discuss system architecture, components, and technical designs to generate diagrams
        </p>
      </div>
    </div>
  );
}
