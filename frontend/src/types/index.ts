export interface Message {
  id: number;
  conversation_id: number;
  content: string;
  user_id: string;
  user_name: string | null;
  timestamp: string;
  is_technical: boolean;
  confidence_score: number;
  entities: string | null;
}

export interface Conversation {
  id: number;
  platform: 'web' | 'teams';
  channel_id: string | null;
  thread_id: string | null;
  created_at: string;
  updated_at: string | null;
  messages: Message[];
}

export interface Diagram {
  id: number;
  conversation_id: number;
  plantuml_code: string | null;
  drawio_xml: string | null;
  png_url: string | null;
  version: number;
  created_at: string;
  components_count: number;
  relationships_count: number;
}

export interface ModificationRequest {
  diagram_id: number;
  request: string;
  user_id?: string;
}

export interface ModificationResponse {
  id: number;
  diagram_id: number;
  request: string;
  applied_at: string;
  success: boolean;
  error_message: string | null;
  new_diagram: Diagram | null;
}

export interface WebSocketMessage {
  type: 'message' | 'diagram_generation_started' | 'diagram_generated' | 'diagram_generation_failed';
  data?: any;
  conversation_id?: number;
  diagram_id?: number;
  error?: string;
}
