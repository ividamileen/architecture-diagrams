import React, { useState, useEffect } from 'react';
import { ChatInterface } from '../components/ChatInterface';
import { DiagramViewer } from '../components/DiagramViewer';
import { conversationsApi, messagesApi, diagramsApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Message, Diagram } from '../types';
import toast, { Toaster } from 'react-hot-toast';
import { Loader2 } from 'lucide-react';

export function HomePage() {
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentDiagram, setCurrentDiagram] = useState<Diagram | null>(null);
  const [loading, setLoading] = useState(true);

  const { lastMessage } = useWebSocket(conversationId);

  // Initialize conversation
  useEffect(() => {
    const initConversation = async () => {
      try {
        // Create a new web conversation
        const conversation = await conversationsApi.create({ platform: 'web' });
        setConversationId(conversation.id);

        // Load existing messages (if any)
        const existingMessages = await messagesApi.getByConversation(conversation.id);
        setMessages(existingMessages);

        // Load existing diagrams (if any)
        const diagrams = await diagramsApi.getByConversation(conversation.id);
        if (diagrams.length > 0) {
          setCurrentDiagram(diagrams[0]);
        }
      } catch (error) {
        console.error('Error initializing conversation:', error);
        toast.error('Failed to initialize conversation');
      } finally {
        setLoading(false);
      }
    };

    initConversation();
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case 'message':
        if (lastMessage.data) {
          setMessages((prev) => [...prev, lastMessage.data]);
        }
        break;

      case 'diagram_generation_started':
        toast.loading('Generating diagram...', { id: 'diagram-gen' });
        break;

      case 'diagram_generated':
        toast.success('Diagram generated!', { id: 'diagram-gen' });
        if (lastMessage.diagram_id) {
          loadDiagram(lastMessage.diagram_id);
        }
        break;

      case 'diagram_generation_failed':
        toast.error('Failed to generate diagram', { id: 'diagram-gen' });
        break;
    }
  }, [lastMessage]);

  const loadDiagram = async (diagramId: number) => {
    try {
      const diagram = await diagramsApi.get(diagramId);
      setCurrentDiagram(diagram);
    } catch (error) {
      console.error('Error loading diagram:', error);
    }
  };

  const handleMessageSent = (message: Message) => {
    setMessages((prev) => [...prev, message]);

    // Check if diagram generation should be triggered
    if (message.is_technical && message.confidence_score >= 0.7) {
      // Count recent technical messages
      const recentTechnical = messages.filter(
        (m) => m.is_technical && m.confidence_score >= 0.7
      );

      if (recentTechnical.length >= 2) {
        // Trigger diagram generation
        generateDiagram();
      }
    }
  };

  const generateDiagram = async () => {
    if (!conversationId) return;

    toast.loading('Generating diagram...', { id: 'diagram-gen' });
    try {
      const diagram = await diagramsApi.generate({
        conversation_id: conversationId,
        force_regenerate: false,
      });
      setCurrentDiagram(diagram);
      toast.success('Diagram generated!', { id: 'diagram-gen' });
    } catch (error: any) {
      console.error('Error generating diagram:', error);
      if (error.response?.status === 400) {
        toast.error('Not enough technical messages', { id: 'diagram-gen' });
      } else {
        toast.error('Failed to generate diagram', { id: 'diagram-gen' });
      }
    }
  };

  const handleDiagramUpdated = (diagram: Diagram) => {
    setCurrentDiagram(diagram);
    toast.success('Diagram updated!');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
      </div>
    );
  }

  if (!conversationId) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-600">Failed to initialize conversation</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Toaster position="top-right" />

      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Architecture Diagram Generator
            </h1>
            <p className="text-sm text-gray-500">
              AI-powered diagram generation from technical conversations
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">Conversation #{conversationId}</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Interface */}
        <div className="w-1/2 border-r border-gray-200 bg-white">
          <ChatInterface
            conversationId={conversationId}
            messages={messages}
            onMessageSent={handleMessageSent}
            onDiagramGenerationStarted={() =>
              toast.loading('Generating diagram...', { id: 'diagram-gen' })
            }
          />
        </div>

        {/* Diagram Viewer */}
        <div className="w-1/2 bg-white">
          <DiagramViewer
            conversationId={conversationId}
            currentDiagram={currentDiagram}
            onDiagramUpdated={handleDiagramUpdated}
          />
        </div>
      </div>
    </div>
  );
}
