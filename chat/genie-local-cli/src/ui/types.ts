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
  THINKING = 'thinking',
  TOOL_START = 'tool_start',
  TOOL_COMPLETE = 'tool_complete',
  AGENT_START = 'agent_start',
  TEAM_START = 'team_start',
  RUN_START = 'run_start',
  RUN_COMPLETE = 'run_complete',
  MEMORY_UPDATE = 'memory_update',
  RESPONSE_CONTENT = 'response_content',
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
  details?: string; // For error details or additional information
  metadata?: {
    target?: {
      type: 'agent' | 'team' | 'workflow';
      id: string;
      name?: string;
    };
    streaming?: boolean;
    complete?: boolean;
    // Rich event data from API
    event?: string;
    tool?: {
      tool_call_id?: string;
      tool_name: string;
      tool_args?: any;
      tool_result?: any;
      metrics?: {
        time: number;
        tokens?: number;
      };
      created_at?: string;
      agent_id?: string;
      agent_name?: string;
      run_id?: string;
      tool_call_error?: string;
    };
    agent?: {
      agent_id: string;
      agent_name?: string;
      run_id?: string;
      session_id?: string;
      team_session_id?: string;
      model?: string;
      model_provider?: string;
      instructions?: string;
    };
    memory?: {
      type: string;
      content?: string;
      metadata?: any;
    };
    run?: {
      run_id: string;
      status?: string;
      metrics?: any;
    };
    team?: {
      team_id: string;
      team_name?: string;
      run_id?: string;
      model?: string;
      model_provider?: string;
      mode?: string;
    };
    thinking?: {
      content: string;
      reasoning?: string;
    };
    rag?: {
      query?: string;
      results?: any[];
      metadata?: any;
    };
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