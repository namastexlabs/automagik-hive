import { request as gaxiosRequest } from 'gaxios';
import { appConfig } from './settings.js';
import { LocalAPIResponse, StreamingResponse, AgentRequest, TeamRequest } from './localClient.js';

interface RunStats {
  startTime: number;
  endTime?: number;
  totalDuration?: number;
  agentCalls: number;
  toolCalls: number;
  memoryUpdates: number;
  ragQueries: number;
  toolMetrics: Array<{ name: string; duration: number }>;
  eventCounts: Record<string, number>;
  finalMetrics?: any;
}

// Essential events we care about - filter out the noise
const ESSENTIAL_EVENTS = new Set([
  'TeamRunResponseContent',
  'RunResponseContent',
  'TeamRunStarted',
  'RunStarted',
  'TeamToolCallStarted',
  'ToolCallStarted',
  'ToolCallCompleted',
  'TeamToolCallCompleted',
  'TeamRunCompleted',
  'RunCompleted',
  'MemoryUpdateCompleted',
  'RAGQueryCompleted',
  'ThinkingStarted',
  'ThinkingCompleted'
]);

export class OptimizedAPIClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = appConfig.apiBaseUrl;
  }

  private createStreamParser() {
    let buffer = '';
    let stats: RunStats = {
      startTime: Date.now(),
      agentCalls: 0,
      toolCalls: 0,
      memoryUpdates: 0,
      ragQueries: 0,
      toolMetrics: [],
      eventCounts: {}
    };

    return {
      stats,
      parseChunk(chunk: string): any[] {
        buffer += chunk;
        const events: any[] = [];
        
        // Optimized parsing - find complete JSON objects
        let start = 0;
        let braceCount = 0;
        let inString = false;
        let escapeNext = false;
        
        for (let i = 0; i < buffer.length; i++) {
          const char = buffer[i];
          
          if (!inString) {
            if (char === '{') {
              if (braceCount === 0) start = i;
              braceCount++;
            } else if (char === '}') {
              braceCount--;
              if (braceCount === 0) {
                // Found complete object
                const jsonStr = buffer.substring(start, i + 1);
                try {
                  const event = JSON.parse(jsonStr);
                  
                  // Update stats
                  stats.eventCounts[event.event] = (stats.eventCounts[event.event] || 0) + 1;
                  
                  // Only process essential events
                  if (ESSENTIAL_EVENTS.has(event.event)) {
                    events.push(event);
                    
                    // Collect metrics
                    if (event.event === 'RunStarted') stats.agentCalls++;
                    if (event.event === 'ToolCallCompleted' || event.event === 'TeamToolCallCompleted') {
                      stats.toolCalls++;
                      if (event.tool?.metrics?.time) {
                        stats.toolMetrics.push({
                          name: event.tool.tool_name || event.tool_name || 'unknown',
                          duration: event.tool.metrics.time * 1000
                        });
                      }
                    }
                    if (event.event === 'MemoryUpdateCompleted') stats.memoryUpdates++;
                    if (event.event === 'RAGQueryCompleted') stats.ragQueries++;
                    
                    // Capture final metrics
                    if (event.event === 'TeamRunCompleted' || event.event === 'RunCompleted') {
                      stats.endTime = Date.now();
                      stats.totalDuration = stats.endTime - stats.startTime;
                      stats.finalMetrics = event.metrics || event.run_metrics || {};
                    }
                  }
                } catch (e) {
                  // Invalid JSON, skip
                }
              }
            } else if (char === '"' && !escapeNext) {
              inString = true;
            }
          } else {
            if (char === '"' && !escapeNext) {
              inString = false;
            }
            escapeNext = char === '\\' && !escapeNext;
          }
        }
        
        // Keep remaining buffer
        if (braceCount === 0) {
          buffer = '';
        } else {
          buffer = buffer.substring(start);
        }
        
        return events;
      }
    };
  }

  async streamAgent(
    request: AgentRequest,
    onMessage: (data: StreamingResponse) => void,
    onError: (error: Error) => void,
    onComplete: (stats?: RunStats) => void,
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

      const url = `${this.baseUrl}/playground/agents/${request.agent_id}/runs`;
      const response = await gaxiosRequest({
        url,
        method: 'POST',
        data: formData,
        responseType: 'stream',
        timeout: 0,
        signal: abortSignal,
      });

      const parser = this.createStreamParser();
      let sessionId = request.session_id;

      (response.data as any).on('data', (chunk: Buffer) => {
        const events = parser.parseChunk(chunk.toString());
        
        for (const event of events) {
          // Extract session_id
          if (event.session_id && !sessionId) {
            sessionId = event.session_id;
          }
          
          // Handle content events - extract both content and thinking
          if (event.event === 'TeamRunResponseContent' || event.event === 'RunResponseContent') {
            const textContent = event.thinking || event.content || '';
            if (textContent && event.content_type === 'str') {
              onMessage({
                content: textContent,
                done: false,
                session_id: sessionId,
                metadata: { type: 'content' }
              });
            }
          }
          
          // Handle essential status events (reduced verbosity)
          else if (event.event === 'TeamRunStarted') {
            onMessage({
              content: `🔵 ${event.team_name || 'Team'}`,
              done: false,
              session_id: sessionId,
              metadata: { type: 'team_start' }
            });
          }
          else if (event.event === 'RunStarted') {
            onMessage({
              content: `🤖 ${event.agent_name || 'Agent'}`,
              done: false,
              session_id: sessionId,
              metadata: { type: 'agent_start' }
            });
          }
          else if (event.event === 'ToolCallStarted' || event.event === 'TeamToolCallStarted') {
            // Skip showing tool starts to reduce noise
          }
          else if (event.event === 'ToolCallCompleted' || event.event === 'TeamToolCallCompleted') {
            const toolName = event.tool?.tool_name || event.tool_name || 'unknown';
            const duration = event.tool?.metrics?.time ? ` (${(event.tool.metrics.time * 1000).toFixed(0)}ms)` : '';
            onMessage({
              content: `✅ ${toolName}${duration}`,
              done: false,
              session_id: sessionId,
              metadata: { type: 'tool_complete' }
            });
          }
          else if (event.event === 'TeamRunCompleted' || event.event === 'RunCompleted') {
            // Extract final response content if available
            if (event.content && event.content.length > 10) {
              onMessage({
                content: event.content,
                done: false,
                session_id: sessionId,
                metadata: { type: 'content' }
              });
            }
            onComplete(parser.stats);
            return;
          }
        }
      });

      (response.data as any).on('end', () => {
        // Stats already handled in completion event
      });

      (response.data as any).on('error', (error: Error) => {
        onError(error);
      });
      
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }

  async streamTeam(
    request: TeamRequest,
    onMessage: (data: StreamingResponse) => void,
    onError: (error: Error) => void,
    onComplete: (stats?: RunStats) => void,
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

      const url = `${this.baseUrl}/playground/teams/${request.team_id}/runs`;
      const response = await gaxiosRequest({
        url,
        method: 'POST',
        data: formData,
        responseType: 'stream',
        timeout: 0,
        signal: abortSignal,
      });

      const parser = this.createStreamParser();
      let sessionId = request.session_id;

      (response.data as any).on('data', (chunk: Buffer) => {
        const events = parser.parseChunk(chunk.toString());
        
        for (const event of events) {
          // Extract session_id
          if (event.session_id && !sessionId) {
            sessionId = event.session_id;
          }
          
          // Handle content events - extract both content and thinking
          if (event.event === 'TeamRunResponseContent' || event.event === 'RunResponseContent') {
            const textContent = event.thinking || event.content || '';
            if (textContent && event.content_type === 'str') {
              onMessage({
                content: textContent,
                done: false,
                session_id: sessionId,
                metadata: { type: 'content' }
              });
            }
          }
          
          // Handle essential status events (reduced verbosity)
          else if (event.event === 'TeamRunStarted') {
            onMessage({
              content: `🔵 ${event.team_name || 'Team'}`,
              done: false,
              session_id: sessionId,
              metadata: { type: 'team_start' }
            });
          }
          else if (event.event === 'RunStarted') {
            onMessage({
              content: `🤖 ${event.agent_name || 'Agent'}`,
              done: false,
              session_id: sessionId,
              metadata: { type: 'agent_start' }
            });
          }
          else if (event.event === 'ToolCallCompleted' || event.event === 'TeamToolCallCompleted') {
            const toolName = event.tool?.tool_name || event.tool_name || 'unknown';
            const duration = event.tool?.metrics?.time ? ` (${(event.tool.metrics.time * 1000).toFixed(0)}ms)` : '';
            onMessage({
              content: `✅ ${toolName}${duration}`,
              done: false,
              session_id: sessionId,
              metadata: { type: 'tool_complete' }
            });
          }
          else if (event.event === 'TeamRunCompleted') {
            onComplete(parser.stats);
            return;
          }
        }
      });

      (response.data as any).on('end', () => {
        // Stats already handled in completion event
      });

      (response.data as any).on('error', (error: Error) => {
        onError(error);
      });
      
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }

  // Use the original client methods for non-streaming operations
  async listAgents(): Promise<LocalAPIResponse<any[]>> {
    const url = `${this.baseUrl}/playground/agents`;
    const response = await gaxiosRequest({
      url,
      method: 'GET',
      timeout: 5000, // Reduced timeout
    });
    return { data: response.data as any };
  }

  async listTeams(): Promise<LocalAPIResponse<any[]>> {
    const url = `${this.baseUrl}/playground/teams`;
    const response = await gaxiosRequest({
      url,
      method: 'GET',
      timeout: 5000,
    });
    return { data: response.data as any };
  }

  async listWorkflows(): Promise<LocalAPIResponse<any[]>> {
    const url = `${this.baseUrl}/playground/workflows`;
    const response = await gaxiosRequest({
      url,
      method: 'GET',
      timeout: 5000,
    });
    return { data: response.data as any };
  }

  async healthCheck(): Promise<LocalAPIResponse<{ status: string }>> {
    const url = `${this.baseUrl}/api/v1/health`;
    const response = await gaxiosRequest({
      url,
      method: 'GET',
      timeout: 2000,
    });
    return { data: response.data as any };
  }
}

export const optimizedAPIClient = new OptimizedAPIClient();

// Helper function to format stats
export function formatRunStats(stats: RunStats): string {
  if (!stats) return '';
  
  const lines: string[] = [
    '\n📊 Run Statistics:',
    `⏱️  Total Duration: ${stats.totalDuration ? (stats.totalDuration / 1000).toFixed(2) + 's' : 'N/A'}`,
    `🤖 Agents Called: ${stats.agentCalls}`,
    `🔧 Tools Executed: ${stats.toolCalls}`,
    `🧠 Memory Updates: ${stats.memoryUpdates}`,
    `🔍 RAG Queries: ${stats.ragQueries}`,
  ];
  
  if (stats.toolMetrics.length > 0) {
    lines.push('\n⚡ Tool Performance:');
    const sortedTools = stats.toolMetrics.sort((a, b) => b.duration - a.duration);
    sortedTools.slice(0, 5).forEach(tool => {
      lines.push(`   ${tool.name}: ${tool.duration.toFixed(0)}ms`);
    });
    if (sortedTools.length > 5) {
      lines.push(`   ... and ${sortedTools.length - 5} more`);
    }
  }
  
  if (stats.eventCounts && Object.keys(stats.eventCounts).length > 0) {
    const totalEvents = Object.values(stats.eventCounts).reduce((sum, count) => sum + count, 0);
    lines.push(`\n📈 Total Events Processed: ${totalEvents}`);
  }
  
  return lines.join('\n');
}