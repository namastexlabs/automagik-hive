import { request as gaxiosRequest, GaxiosOptions, GaxiosResponse } from 'gaxios';
import { appConfig } from './settings.js';

export interface LocalAPIResponse<T = any> {
  data: T;
  error?: string;
  session_id?: string;
}

export interface StreamingResponse {
  content: string;
  done: boolean;
  session_id?: string;
  metadata?: Record<string, any>;
}

export interface AgentRequest {
  agent_id: string;
  message: string;
  session_id?: string;
  user_id?: string;
  user_name?: string;
  phone_number?: string;
  cpf?: string;
}

export interface TeamRequest {
  team_id: string;
  message: string;
  session_id?: string;
  user_id?: string;
  user_name?: string;
  phone_number?: string;
  cpf?: string;
}

export interface WorkflowRequest {
  workflow_id: string;
  params: Record<string, any>;
  session_id?: string;
  user_id?: string;
  user_name?: string;
  phone_number?: string;
  cpf?: string;
}

export class LocalAPIClient {
  private baseUrl: string;
  private timeout: number;
  private retryAttempts: number;

  constructor() {
    this.baseUrl = appConfig.apiBaseUrl;
    this.timeout = appConfig.apiTimeout;
    this.retryAttempts = appConfig.apiRetryAttempts;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: Partial<GaxiosOptions> = {}
  ): Promise<LocalAPIResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response: GaxiosResponse<T> = await gaxiosRequest({
        url,
        timeout: this.timeout,
        ...options,
      });

      return {
        data: response.data,
        session_id: response.headers.get('x-session-id') || (response.data as any)?.session_id || undefined,
      };
    } catch (error) {
      if (appConfig.cliDebug) {
        console.error('API Request failed:', error);
      }
      
      return {
        data: null as T,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // Fetch OpenAPI schema
  async getSchema(): Promise<LocalAPIResponse<any>> {
    return this.makeRequest('/openapi.json', {
      method: 'GET',
    });
  }

  // List available agents
  async listAgents(): Promise<LocalAPIResponse<any[]>> {
    return this.makeRequest('/playground/agents', {
      method: 'GET',
    });
  }

  // List available teams
  async listTeams(): Promise<LocalAPIResponse<any[]>> {
    return this.makeRequest('/playground/teams', {
      method: 'GET',
    });
  }

  // List available workflows
  async listWorkflows(): Promise<LocalAPIResponse<any[]>> {
    return this.makeRequest('/playground/workflows', {
      method: 'GET',
    });
  }

  // Invoke an agent (non-streaming)
  async invokeAgent(request: AgentRequest): Promise<LocalAPIResponse<any>> {
    const formData = new FormData();
    formData.append('message', request.message);
    formData.append('stream', 'false');
    if (request.session_id) {
      formData.append('session_id', request.session_id);
    }
    if (request.user_id) {
      formData.append('user_id', request.user_id);
    }
    if (request.user_name) {
      formData.append('user_name', request.user_name);
    }
    if (request.phone_number) {
      formData.append('phone_number', request.phone_number);
    }
    if (request.cpf) {
      formData.append('cpf', request.cpf);
    }

    return this.makeRequest(`/playground/agents/${request.agent_id}/runs`, {
      method: 'POST',
      data: formData,
      headers: {
        // Don't set Content-Type, let browser set it with boundary for multipart
      },
    });
  }

  // Invoke a team (non-streaming)
  async invokeTeam(request: TeamRequest): Promise<LocalAPIResponse<any>> {
    const formData = new FormData();
    formData.append('message', request.message);
    formData.append('stream', 'false');
    if (request.session_id) {
      formData.append('session_id', request.session_id);
    }
    if (request.user_id) {
      formData.append('user_id', request.user_id);
    }
    if (request.user_name) {
      formData.append('user_name', request.user_name);
    }
    if (request.phone_number) {
      formData.append('phone_number', request.phone_number);
    }
    if (request.cpf) {
      formData.append('cpf', request.cpf);
    }

    return this.makeRequest(`/playground/teams/${request.team_id}/runs`, {
      method: 'POST',
      data: formData,
      headers: {
        // Don't set Content-Type, let browser set it with boundary for multipart
      },
    });
  }

  // Execute a workflow (non-streaming)
  async executeWorkflow(request: WorkflowRequest): Promise<LocalAPIResponse<any>> {
    return this.makeRequest(`/playground/workflows/${request.workflow_id}/runs`, {
      method: 'POST',
      data: {
        params: request.params,
        session_id: request.session_id,
        user_id: request.user_id,
        user_name: request.user_name,
        phone_number: request.phone_number,
        cpf: request.cpf,
      },
    });
  }

  // Stream agent response with real API streaming
  async streamAgent(
    request: AgentRequest,
    onMessage: (data: StreamingResponse) => void,
    onError: (error: Error) => void,
    onComplete: () => void,
    abortSignal?: AbortSignal
  ): Promise<void> {
    try {
      const formData = new FormData();
      formData.append('message', request.message);
      formData.append('stream', 'true');
      formData.append('monitor', 'true');
      if (request.session_id) {
        formData.append('session_id', request.session_id);
      }
      if (request.user_id) {
        formData.append('user_id', request.user_id);
      }
      if (request.user_name) {
        formData.append('user_name', request.user_name);
      }
      if (request.phone_number) {
        formData.append('phone_number', request.phone_number);
      }
      if (request.cpf) {
        formData.append('cpf', request.cpf);
      }

      const url = `${this.baseUrl}/playground/agents/${request.agent_id}/runs`;
      
      const response = await gaxiosRequest({
        url,
        method: 'POST',
        data: formData,
        responseType: 'stream',
        timeout: 0, // No timeout for streaming requests
        signal: abortSignal,
      });

      let buffer = '';
      let finalContent = '';
      let sessionId = request.session_id;

      (response.data as any).on('data', (chunk: Buffer) => {
        const chunkStr = chunk.toString();
        if (appConfig.cliDebug) {
          console.log('[STREAM CHUNK]:', chunkStr.slice(0, 200) + (chunkStr.length > 200 ? '...' : ''));
        }
        buffer += chunkStr;
        
        // Process complete JSON objects in buffer
        // JSON objects are separated by }{ not newlines
        let separatorIndex;
        while ((separatorIndex = buffer.indexOf('}{')) !== -1) {
          const jsonStr = buffer.slice(0, separatorIndex + 1).trim();
          buffer = '{' + buffer.slice(separatorIndex + 2); // Keep the opening { for next object
          
          if (jsonStr) {
            try {
              const event = JSON.parse(jsonStr);
              if (appConfig.cliDebug) {
                console.log('[EVENT]:', event.event, event.content ? `"${event.content.slice(0, 50)}..."` : '');
                console.log('[EVENT DATA]:', JSON.stringify(event, null, 2));
              }
              
              // Extract session_id from first event
              if (event.session_id && !sessionId) {
                sessionId = event.session_id;
              }
              
              // Handle content events (including thinking)
              if (event.event === 'TeamRunResponseContent' || event.event === 'RunResponseContent') {
                if (event.content) {
                  // Handle both regular content and thinking content
                  const content = event.content;
                  if (event.content_type === 'str') {
                    finalContent += content;
                  }
                  onMessage({
                    content: content,
                    done: false,
                    session_id: sessionId,
                    metadata: {
                      type: 'content',
                      event: event.event,
                      content_type: event.content_type,
                    },
                  });
                }
              }
              
              // Handle team start events
              if (event.event === 'TeamRunStarted') {
                const teamName = event.team_name || event.team_id || event.team?.team_name || event.team?.team_id || 'unknown';
                onMessage({
                  content: `🔵 ${teamName}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'team_start',
                    event: event.event,
                    team: {
                      team_id: event.team_id,
                      team_name: event.team_name,
                      run_id: event.run_id,
                      model: event.model,
                      model_provider: event.model_provider,
                    },
                  },
                });
              }
              
              // Handle tool call events
              if (event.event === 'TeamToolCallStarted' || event.event === 'ToolCallStarted') {
                const toolName = event.tool?.tool_name || event.tool_name || 'unknown';
                const toolArgs = event.tool?.tool_args || event.tool_args || {};
                const argsStr = Object.keys(toolArgs).length > 0 ? JSON.stringify(toolArgs, null, 2) : '';
                onMessage({
                  content: `🔧 ${toolName}${argsStr ? '\n\nArguments:\n' + argsStr : ''}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'tool_start',
                    event: event.event,
                    tool: {
                      tool_call_id: event.tool?.tool_call_id,
                      tool_name: event.tool?.tool_name || event.tool_name,
                      tool_args: event.tool?.tool_args || event.tool_args,
                      created_at: event.tool?.created_at || event.created_at,
                      agent_id: event.agent_id,
                      agent_name: event.agent_name,
                      run_id: event.run_id,
                    },
                  },
                });
              }
              
              if (event.event === 'ToolCallCompleted' || event.event === 'TeamToolCallCompleted') {
                const toolName = event.tool?.tool_name || event.tool_name || 'unknown';
                const duration = event.tool?.metrics?.time ? ` (${(event.tool.metrics.time * 1000).toFixed(0)}ms)` : '';
                const toolResult = event.tool?.result || event.tool?.tool_result || event.tool_result || event.result;
                const resultStr = toolResult && typeof toolResult === 'string' && toolResult.trim() ? 
                  (toolResult.length > 500 ? toolResult.substring(0, 500) + '...' : toolResult) : '';
                onMessage({
                  content: `✅ ${toolName}${duration}${resultStr ? '\n\nResult:\n' + resultStr : ''}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'tool_complete',
                    event: event.event,
                    tool: {
                      tool_call_id: event.tool?.tool_call_id,
                      tool_name: event.tool?.tool_name || event.tool_name,
                      tool_args: event.tool?.tool_args || event.tool_args,
                      tool_result: event.tool?.result || event.tool?.tool_result || event.tool_result || event.result,
                      metrics: event.tool?.metrics || event.metrics,
                      created_at: event.tool?.created_at || event.created_at,
                      agent_id: event.agent_id,
                      agent_name: event.agent_name,
                      run_id: event.run_id,
                      tool_call_error: event.tool?.tool_call_error,
                    },
                  },
                });
              }
              
              // Handle agent start events
              if (event.event === 'RunStarted') {
                const agentName = event.agent_name || event.agent?.agent_name || event.agent_id || event.agent?.agent_id || 'unknown';
                onMessage({
                  content: `🤖 ${agentName}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'agent_start',
                    event: event.event,
                    agent: {
                      agent_id: event.agent_id,
                      agent_name: event.agent_name,
                      run_id: event.run_id,
                      session_id: event.session_id,
                      team_session_id: event.team_session_id,
                      model: event.model,
                      model_provider: event.model_provider,
                    },
                  },
                });
              }
              
              // Handle memory events
              if (event.event === 'MemoryUpdateStarted' || event.event === 'MemoryUpdateCompleted') {
                const memoryType = event.memory_type || event.memory?.type || event.type || 'user memory';
                const action = event.event === 'MemoryUpdateStarted' ? 'Updating' : 'Updated';
                const memoryContent = event.memory_content || event.content || event.memory?.content || '';
                
                // Debug logging for memory events
                if (appConfig.cliDebug) {
                  console.log('[MEMORY EVENT DEBUG]:', {
                    event: event.event,
                    memory_type: event.memory_type,
                    memory_content: event.memory_content,
                    content: event.content,
                    memory: event.memory,
                    type: event.type,
                    extractedType: memoryType,
                    extractedContent: memoryContent,
                  });
                }
                
                onMessage({
                  content: `🧠 ${action} ${memoryType}${memoryContent ? '\n\nContent:\n' + memoryContent : ''}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'memory_update',
                    event: event.event,
                    eventId: `${event.event}-${Date.now()}-${Math.random()}`, // Unique event ID
                    memory: event.memory || {
                      type: event.memory_type || event.type,
                      content: event.memory_content || event.content,
                      metadata: event.metadata,
                    },
                  },
                });
              }
              
              // Handle thinking events
              if (event.event === 'ThinkingStarted' || event.event === 'ThinkingCompleted') {
                const thinkingAction = event.event === 'ThinkingStarted' ? 'Thinking...' : 'Thought complete';
                onMessage({
                  content: `🤔 ${thinkingAction}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'thinking',
                    event: event.event,
                    thinking: {
                      content: event.content || '',
                      reasoning: event.reasoning || '',
                    },
                  },
                });
              }
              
              // Handle RAG events
              if (event.event === 'RAGQueryStarted' || event.event === 'RAGQueryCompleted') {
                const ragAction = event.event === 'RAGQueryStarted' ? 'Searching' : 'Found';
                const query = event.query || 'knowledge base';
                onMessage({
                  content: `🔍 ${ragAction} in ${query}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'rag_query',
                    event: event.event,
                    rag: {
                      query: event.query,
                      results: event.results,
                      metadata: event.metadata,
                    },
                  },
                });
              }
              
              // Handle completion events
              if (event.event === 'TeamRunCompleted' || event.event === 'RunCompleted') {
                onMessage({
                  content: '',
                  done: true,
                  session_id: sessionId,
                });
                onComplete();
                return;
              }
              
            } catch (parseError) {
              console.warn('Failed to parse JSON:', jsonStr?.slice(0, 100));
            }
          }
        }
      });

      (response.data as any).on('end', () => {
        // Process any remaining JSON in buffer
        if (buffer.trim()) {
          try {
            const event = JSON.parse(buffer.trim());
            if (appConfig.cliDebug) {
              console.log('[FINAL EVENT]:', event.event);
            }
            
            // Handle final content events
            if (event.event === 'TeamRunResponseContent' || event.event === 'RunResponseContent') {
              if (event.content) {
                const content = event.content;
                if (event.content_type === 'str') {
                  finalContent += content;
                }
                onMessage({
                  content: content,
                  done: false,
                  session_id: sessionId,
                });
              }
            }
            
            // Handle completion events
            if (event.event === 'TeamRunCompleted' || event.event === 'RunCompleted') {
              onMessage({
                content: '',
                done: true,
                session_id: sessionId,
              });
              onComplete();
              return;
            }
          } catch (parseError) {
            console.warn('Failed to parse final JSON:', buffer.slice(0, 100));
          }
        }
        
        // Complete anyway
        onMessage({
          content: '',
          done: true,
          session_id: sessionId,
        });
        onComplete();
      });

      (response.data as any).on('error', (error: Error) => {
        if (appConfig.cliDebug) {
          console.log('[STREAM ERROR]:', error.message);
        }
        // Don't treat timeout/abort as fatal error if we got some content
        if (error.message.includes('aborted') || error.message.includes('timeout')) {
          onMessage({
            content: '\n⚠️ Stream interrupted - response may be incomplete',
            done: true,
            session_id: sessionId,
          });
          onComplete();
        } else {
          onError(error);
        }
      });
      
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }

  // Stream team response with real API streaming
  async streamTeam(
    request: TeamRequest,
    onMessage: (data: StreamingResponse) => void,
    onError: (error: Error) => void,
    onComplete: () => void,
    abortSignal?: AbortSignal
  ): Promise<void> {
    try {
      const formData = new FormData();
      formData.append('message', request.message);
      formData.append('stream', 'true');
      formData.append('monitor', 'true');
      if (request.session_id) {
        formData.append('session_id', request.session_id);
      }
      if (request.user_id) {
        formData.append('user_id', request.user_id);
      }
      if (request.user_name) {
        formData.append('user_name', request.user_name);
      }
      if (request.phone_number) {
        formData.append('phone_number', request.phone_number);
      }
      if (request.cpf) {
        formData.append('cpf', request.cpf);
      }

      const url = `${this.baseUrl}/playground/teams/${request.team_id}/runs`;
      
      const response = await gaxiosRequest({
        url,
        method: 'POST',
        data: formData,
        responseType: 'stream',
        timeout: 0, // No timeout for streaming requests
        signal: abortSignal,
      });

      let buffer = '';
      let finalContent = '';
      let sessionId = request.session_id;

      (response.data as any).on('data', (chunk: Buffer) => {
        buffer += chunk.toString();
        
        // Process complete JSON objects in buffer
        // JSON objects are separated by }{ not newlines
        let separatorIndex;
        while ((separatorIndex = buffer.indexOf('}{')) !== -1) {
          const jsonStr = buffer.slice(0, separatorIndex + 1).trim();
          buffer = '{' + buffer.slice(separatorIndex + 2); // Keep the opening { for next object
          
          if (jsonStr) {
            try {
              const event = JSON.parse(jsonStr);
              
              // Extract session_id from first event
              if (event.session_id && !sessionId) {
                sessionId = event.session_id;
              }
              
              // Handle content events (including thinking)
              if (event.event === 'TeamRunResponseContent' || event.event === 'RunResponseContent') {
                if (event.content) {
                  // Handle both regular content and thinking content
                  const content = event.content;
                  if (event.content_type === 'str') {
                    finalContent += content;
                  }
                  onMessage({
                    content: content,
                    done: false,
                    session_id: sessionId,
                    metadata: {
                      type: 'content',
                      event: event.event,
                      content_type: event.content_type,
                    },
                  });
                }
              }
              
              // Handle team start events
              if (event.event === 'TeamRunStarted') {
                const teamName = event.team_name || event.team_id || event.team?.team_name || event.team?.team_id || 'unknown';
                onMessage({
                  content: `🔵 ${teamName}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'team_start',
                    event: event.event,
                    team: {
                      team_id: event.team_id,
                      team_name: event.team_name,
                      run_id: event.run_id,
                      model: event.model,
                      model_provider: event.model_provider,
                    },
                  },
                });
              }
              
              // Handle tool call events
              if (event.event === 'TeamToolCallStarted' || event.event === 'ToolCallStarted') {
                const toolName = event.tool?.tool_name || event.tool_name || 'unknown';
                const toolArgs = event.tool?.tool_args || event.tool_args || {};
                const argsStr = Object.keys(toolArgs).length > 0 ? JSON.stringify(toolArgs, null, 2) : '';
                onMessage({
                  content: `🔧 ${toolName}${argsStr ? '\n\nArguments:\n' + argsStr : ''}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'tool_start',
                    event: event.event,
                    tool: {
                      tool_call_id: event.tool?.tool_call_id,
                      tool_name: event.tool?.tool_name || event.tool_name,
                      tool_args: event.tool?.tool_args || event.tool_args,
                      created_at: event.tool?.created_at || event.created_at,
                      agent_id: event.agent_id,
                      agent_name: event.agent_name,
                      run_id: event.run_id,
                    },
                  },
                });
              }
              
              if (event.event === 'ToolCallCompleted' || event.event === 'TeamToolCallCompleted') {
                const toolName = event.tool?.tool_name || event.tool_name || 'unknown';
                const duration = event.tool?.metrics?.time ? ` (${(event.tool.metrics.time * 1000).toFixed(0)}ms)` : '';
                const toolResult = event.tool?.result || event.tool?.tool_result || event.tool_result || event.result;
                const resultStr = toolResult && typeof toolResult === 'string' && toolResult.trim() ? 
                  (toolResult.length > 500 ? toolResult.substring(0, 500) + '...' : toolResult) : '';
                onMessage({
                  content: `✅ ${toolName}${duration}${resultStr ? '\n\nResult:\n' + resultStr : ''}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'tool_complete',
                    event: event.event,
                    tool: {
                      tool_call_id: event.tool?.tool_call_id,
                      tool_name: event.tool?.tool_name || event.tool_name,
                      tool_args: event.tool?.tool_args || event.tool_args,
                      tool_result: event.tool?.result || event.tool?.tool_result || event.tool_result || event.result,
                      metrics: event.tool?.metrics || event.metrics,
                      created_at: event.tool?.created_at || event.created_at,
                      agent_id: event.agent_id,
                      agent_name: event.agent_name,
                      run_id: event.run_id,
                      tool_call_error: event.tool?.tool_call_error,
                    },
                  },
                });
              }
              
              // Handle agent start events
              if (event.event === 'RunStarted') {
                const agentName = event.agent_name || event.agent?.agent_name || event.agent_id || event.agent?.agent_id || 'unknown';
                onMessage({
                  content: `🤖 ${agentName}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'agent_start',
                    event: event.event,
                    agent: {
                      agent_id: event.agent_id,
                      agent_name: event.agent_name,
                      run_id: event.run_id,
                      session_id: event.session_id,
                      team_session_id: event.team_session_id,
                      model: event.model,
                      model_provider: event.model_provider,
                    },
                  },
                });
              }
              
              // Handle memory events
              if (event.event === 'MemoryUpdateStarted' || event.event === 'MemoryUpdateCompleted') {
                const memoryType = event.memory_type || event.memory?.type || event.type || 'user memory';
                const action = event.event === 'MemoryUpdateStarted' ? 'Updating' : 'Updated';
                const memoryContent = event.memory_content || event.content || event.memory?.content || '';
                
                // Debug logging for memory events
                if (appConfig.cliDebug) {
                  console.log('[MEMORY EVENT DEBUG]:', {
                    event: event.event,
                    memory_type: event.memory_type,
                    memory_content: event.memory_content,
                    content: event.content,
                    memory: event.memory,
                    type: event.type,
                    extractedType: memoryType,
                    extractedContent: memoryContent,
                  });
                }
                
                onMessage({
                  content: `🧠 ${action} ${memoryType}${memoryContent ? '\n\nContent:\n' + memoryContent : ''}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'memory_update',
                    event: event.event,
                    eventId: `${event.event}-${Date.now()}-${Math.random()}`, // Unique event ID
                    memory: event.memory || {
                      type: event.memory_type || event.type,
                      content: event.memory_content || event.content,
                      metadata: event.metadata,
                    },
                  },
                });
              }
              
              // Handle thinking events
              if (event.event === 'ThinkingStarted' || event.event === 'ThinkingCompleted') {
                const thinkingAction = event.event === 'ThinkingStarted' ? 'Thinking...' : 'Thought complete';
                onMessage({
                  content: `🤔 ${thinkingAction}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'thinking',
                    event: event.event,
                    thinking: {
                      content: event.content || '',
                      reasoning: event.reasoning || '',
                    },
                  },
                });
              }
              
              // Handle RAG events
              if (event.event === 'RAGQueryStarted' || event.event === 'RAGQueryCompleted') {
                const ragAction = event.event === 'RAGQueryStarted' ? 'Searching' : 'Found';
                const query = event.query || 'knowledge base';
                onMessage({
                  content: `🔍 ${ragAction} in ${query}`,
                  done: false,
                  session_id: sessionId,
                  metadata: {
                    type: 'rag_query',
                    event: event.event,
                    rag: {
                      query: event.query,
                      results: event.results,
                      metadata: event.metadata,
                    },
                  },
                });
              }
              
              // Handle completion events
              if (event.event === 'TeamRunCompleted') {
                onMessage({
                  content: '',
                  done: true,
                  session_id: sessionId,
                });
                onComplete();
                return;
              }
              
            } catch (parseError) {
              console.warn('Failed to parse JSON:', jsonStr?.slice(0, 100));
            }
          }
        }
      });

      (response.data as any).on('end', () => {
        // Process any remaining JSON in buffer
        if (buffer.trim()) {
          try {
            const event = JSON.parse(buffer.trim());
            if (appConfig.cliDebug) {
              console.log('[FINAL EVENT]:', event.event);
            }
            
            // Handle final content events
            if (event.event === 'TeamRunResponseContent' || event.event === 'RunResponseContent') {
              if (event.content) {
                const content = event.content;
                if (event.content_type === 'str') {
                  finalContent += content;
                }
                onMessage({
                  content: content,
                  done: false,
                  session_id: sessionId,
                });
              }
            }
            
            // Handle completion events
            if (event.event === 'TeamRunCompleted' || event.event === 'RunCompleted') {
              onMessage({
                content: '',
                done: true,
                session_id: sessionId,
              });
              onComplete();
              return;
            }
          } catch (parseError) {
            console.warn('Failed to parse final JSON:', buffer.slice(0, 100));
          }
        }
        
        // Complete anyway
        onMessage({
          content: '',
          done: true,
          session_id: sessionId,
        });
        onComplete();
      });

      (response.data as any).on('error', (error: Error) => {
        if (appConfig.cliDebug) {
          console.log('[STREAM ERROR]:', error.message);
        }
        // Don't treat timeout/abort as fatal error if we got some content
        if (error.message.includes('aborted') || error.message.includes('timeout')) {
          onMessage({
            content: '\n⚠️ Stream interrupted - response may be incomplete',
            done: true,
            session_id: sessionId,
          });
          onComplete();
        } else {
          onError(error);
        }
      });
      
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }

  // Health check
  async healthCheck(): Promise<LocalAPIResponse<{ status: string }>> {
    return this.makeRequest('/api/v1/health', {
      method: 'GET',
    });
  }
}

export const localAPIClient = new LocalAPIClient();