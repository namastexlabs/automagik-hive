export enum StreamingState {
  Idle = 'idle',
  Connecting = 'connecting',
  Waiting = 'waiting',
  Responding = 'responding',
  Error = 'error',
}

export enum MessageType {
  USER = 'user',
  ASSISTANT = 'assistant',
  INFO = 'info',
  ERROR = 'error',
  SYSTEM = 'system',
}

export interface HistoryItem {
  id: number;
  type: MessageType;
  text: string;
  timestamp: number;
  sessionId?: string;
  metadata?: {
    target?: {
      type: 'agent' | 'team' | 'workflow';
      id: string;
    };
    streaming?: boolean;
    complete?: boolean;
  };
}

export interface TargetInfo {
  type: 'agent' | 'team' | 'workflow';
  id: string;
  name?: string;
  description?: string;
}

export interface SessionData {
  id: string;
  messages: HistoryItem[];
  createdAt: number;
  updatedAt: number;
  metadata?: {
    totalMessages: number;
    lastTarget?: TargetInfo;
  };
}

export interface APITarget {
  type: 'agent' | 'team' | 'workflow';
  id: string;
}

export interface StreamingMessage {
  content: string;
  done: boolean;
  sessionId?: string;
  metadata?: Record<string, any>;
}