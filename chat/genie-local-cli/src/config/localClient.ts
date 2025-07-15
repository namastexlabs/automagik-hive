import { request, GaxiosOptions, GaxiosResponse } from 'gaxios';
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
}

export interface AgentRequest {
  agent_id: string;
  message: string;
  session_id?: string;
}

export interface TeamRequest {
  team_id: string;
  message: string;
  session_id?: string;
}

export interface WorkflowRequest {
  workflow_id: string;
  params: Record<string, any>;
  session_id?: string;
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
      const response: GaxiosResponse<T> = await request({
        url,
        timeout: this.timeout,
        ...options,
      });

      return {
        data: response.data,
        session_id: response.headers['x-session-id'] as string,
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
  async listAgents(): Promise<LocalAPIResponse<string[]>> {
    return this.makeRequest('/agents', {
      method: 'GET',
    });
  }

  // List available teams
  async listTeams(): Promise<LocalAPIResponse<string[]>> {
    return this.makeRequest('/teams', {
      method: 'GET',
    });
  }

  // List available workflows
  async listWorkflows(): Promise<LocalAPIResponse<string[]>> {
    return this.makeRequest('/workflows', {
      method: 'GET',
    });
  }

  // Invoke an agent (non-streaming)
  async invokeAgent(request: AgentRequest): Promise<LocalAPIResponse<any>> {
    return this.makeRequest(`/agents/${request.agent_id}/runs`, {
      method: 'POST',
      data: {
        message: request.message,
        session_id: request.session_id,
      },
    });
  }

  // Invoke a team (non-streaming)
  async invokeTeam(request: TeamRequest): Promise<LocalAPIResponse<any>> {
    return this.makeRequest(`/teams/${request.team_id}/runs`, {
      method: 'POST',
      data: {
        message: request.message,
        session_id: request.session_id,
      },
    });
  }

  // Execute a workflow (non-streaming)
  async executeWorkflow(request: WorkflowRequest): Promise<LocalAPIResponse<any>> {
    return this.makeRequest(`/workflows/${request.workflow_id}/runs`, {
      method: 'POST',
      data: {
        params: request.params,
        session_id: request.session_id,
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

  // Stream agent response
  async streamAgent(
    request: AgentRequest,
    onMessage: (data: StreamingResponse) => void,
    onError: (error: Error) => void,
    onComplete: () => void
  ): Promise<void> {
    // For now, implement polling-based streaming as fallback
    // This can be enhanced when WebSocket streaming is available
    try {
      const response = await this.invokeAgent(request);
      
      if (response.error) {
        onError(new Error(response.error));
        return;
      }

      // Simulate streaming by chunking the response
      const content = response.data?.content || '';
      const chunks = content.match(/.{1,10}/g) || [content];
      
      for (let i = 0; i < chunks.length; i++) {
        const chunk = chunks[i];
        setTimeout(() => {
          onMessage({
            content: chunk,
            done: i === chunks.length - 1,
            session_id: response.session_id,
          });
          
          if (i === chunks.length - 1) {
            onComplete();
          }
        }, i * appConfig.streamDelay);
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }

  // Health check
  async healthCheck(): Promise<LocalAPIResponse<{ status: string }>> {
    return this.makeRequest('/health', {
      method: 'GET',
    });
  }
}

export const localAPIClient = new LocalAPIClient();