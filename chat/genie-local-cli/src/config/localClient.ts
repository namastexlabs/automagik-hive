import { request as gaxiosRequest, GaxiosOptions, GaxiosResponse } from 'gaxios';
import WebSocket from 'ws';
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

  // Create streaming connection
  createStreamingConnection(
    onMessage: (data: StreamingResponse) => void,
    onError: (error: Error) => void,
    onClose: () => void
  ): WebSocket {
    const ws = new WebSocket(appConfig.wsUrl);

    ws.on('message', (data) => {
      try {
        const parsed = JSON.parse(data.toString()) as StreamingResponse;
        onMessage(parsed);
      } catch (error) {
        onError(new Error('Failed to parse streaming response'));
      }
    });

    ws.on('error', onError);
    ws.on('close', onClose);

    return ws;
  }

  // Stream agent response with real API streaming
  async streamAgent(
    request: AgentRequest,
    onMessage: (data: StreamingResponse) => void,
    onError: (error: Error) => void,
    onComplete: () => void
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
                  });
                }
              }
              
              // Handle tool call events
              if (event.event === 'TeamToolCallStarted' || event.event === 'ToolCallStarted') {
                const toolName = event.tool?.tool_name || 'unknown';
                onMessage({
                  content: `🔧 Starting tool: ${toolName}`,
                  done: false,
                  session_id: sessionId,
                });
              }
              
              if (event.event === 'ToolCallCompleted') {
                const toolName = event.tool?.tool_name || 'unknown';
                const duration = event.tool?.metrics?.time ? ` (${(event.tool.metrics.time * 1000).toFixed(0)}ms)` : '';
                onMessage({
                  content: `✅ Completed tool: ${toolName}${duration}`,
                  done: false,
                  session_id: sessionId,
                });
              }
              
              // Handle agent start events
              if (event.event === 'RunStarted') {
                const agentName = event.agent_name || event.agent_id || 'unknown';
                onMessage({
                  content: `🤖 Starting agent: ${agentName}`,
                  done: false,
                  session_id: sessionId,
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
    onComplete: () => void
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
                  });
                }
              }
              
              // Handle tool call events
              if (event.event === 'TeamToolCallStarted' || event.event === 'ToolCallStarted') {
                const toolName = event.tool?.tool_name || 'unknown';
                onMessage({
                  content: `🔧 Starting tool: ${toolName}`,
                  done: false,
                  session_id: sessionId,
                });
              }
              
              if (event.event === 'ToolCallCompleted') {
                const toolName = event.tool?.tool_name || 'unknown';
                const duration = event.tool?.metrics?.time ? ` (${(event.tool.metrics.time * 1000).toFixed(0)}ms)` : '';
                onMessage({
                  content: `✅ Completed tool: ${toolName}${duration}`,
                  done: false,
                  session_id: sessionId,
                });
              }
              
              // Handle agent start events
              if (event.event === 'RunStarted') {
                const agentName = event.agent_name || event.agent_id || 'unknown';
                onMessage({
                  content: `🤖 Starting agent: ${agentName}`,
                  done: false,
                  session_id: sessionId,
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