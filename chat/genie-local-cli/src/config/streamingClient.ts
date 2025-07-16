import { request as gaxiosRequest } from 'gaxios';
import { appConfig } from './settings.js';
import { LocalAPIResponse, StreamingResponse, AgentRequest, TeamRequest } from './localClient.js';
import { Transform } from 'stream';

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
  totalTokens?: number;
  latencyBreakdown?: Record<string, number>;
  apiMetrics?: any; // Store API's built-in metrics
}

// Events to completely ignore for performance
const IGNORE_EVENTS = new Set([
  'TeamToolCallStarted',
  'ToolCallStarted',
  'MemoryUpdateStarted',
  'RAGQueryStarted',
  'ThinkingStarted',
]);

export class StreamingAPIClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = appConfig.apiBaseUrl;
  }

  private createRawCollector(): { stats: RunStats; collectChunk: (chunk: string) => void; parseAll: () => any[]; getAllEvents: (buffer: string) => any[] } {
    let rawBuffer = '';
    const stats: RunStats = {
      startTime: Date.now(),
      agentCalls: 0,
      toolCalls: 0,
      memoryUpdates: 0,
      ragQueries: 0,
      toolMetrics: [],
      eventCounts: {}
    };

    function getAllEvents(buffer: string): any[] {
        const allEvents: any[] = [];
        let start = 0;
        let braceCount = 0;
        
        for (let i = 0; i < buffer.length; i++) {
          if (buffer[i] === '{') {
            if (braceCount === 0) start = i;
            braceCount++;
          } else if (buffer[i] === '}') {
            braceCount--;
            if (braceCount === 0) {
              try {
                allEvents.push(JSON.parse(buffer.substring(start, i + 1)));
              } catch (e) {}
            }
          }
        }
        return allEvents;
    }
    
    return {
      stats,
      collectChunk(chunk: string): void {
        rawBuffer += chunk;
      },
      parseAll(): any[] {
        // Post-process stats at the end
        const allEvents = getAllEvents(rawBuffer);
        stats.agentCalls = allEvents.filter((e: any) => e.event === 'RunStarted' || e.event === 'TeamRunStarted').length;
        stats.toolCalls = allEvents.filter((e: any) => e.event === 'ToolCallCompleted' || e.event === 'TeamToolCallCompleted').length;
        stats.memoryUpdates = allEvents.filter((e: any) => e.event === 'MemoryUpdateCompleted').length;
        stats.ragQueries = allEvents.filter((e: any) => e.event === 'RAGQueryCompleted').length;
        
        // Return only content events
        return allEvents.filter((e: any) => e.event === 'TeamRunResponseContent' || e.event === 'RunResponseContent');
      },
      getAllEvents
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
      if (request.session_id) formData.append('session_id', request.session_id);
      if (request.user_id) formData.append('user_id', request.user_id);

      const url = `${this.baseUrl}/playground/agents/${request.agent_id}/runs`;
      const response = await gaxiosRequest({
        url,
        method: 'POST',
        data: formData,
        responseType: 'stream',
        timeout: 0,
        signal: abortSignal,
      });

      const collector = this.createRawCollector();
      const { stats } = collector;
      let sessionId = request.session_id;

      // Handle streaming data - just collect raw data and extract content
      (response.data as any).on('data', (chunk: Buffer) => {
        collector.collectChunk(chunk.toString());
        
        // Fast content extraction 
        const chunkStr = chunk.toString();
        
        // Simple search for content events - look for both RunResponseContent and TeamRunResponseContent
        if (chunkStr.includes('ResponseContent')) {
          const lines = chunkStr.split('\n');
          for (const line of lines) {
            if ((line.includes('RunResponseContent') || line.includes('TeamRunResponseContent')) && line.includes('"content_type":"str"')) {
              try {
                const event = JSON.parse(line);
                // Extract from both thinking and content fields
                const textContent = event.thinking || event.content;
                if (textContent) {
                  onMessage({
                    content: textContent,
                    done: false,
                    session_id: sessionId,
                    metadata: { type: 'content' }
                  });
                }
              } catch (e) {
                // Try regex fallback for both thinking and content
                const thinkingMatch = line.match(/"thinking":"([^"]*)"/);
                const contentMatch = line.match(/"content":"([^"]*)"/);
                const extractedText = thinkingMatch?.[1] || contentMatch?.[1];
                if (extractedText) {
                  onMessage({
                    content: extractedText,
                    done: false,
                    session_id: sessionId,
                    metadata: { type: 'content' }
                  });
                }
              }
            }
          }
        }
        
        // Check for completion and post-process stats
        if (chunkStr.includes('"event":"TeamRunCompleted"') || chunkStr.includes('"event":"RunCompleted"')) {
          stats.endTime = Date.now();
          stats.totalDuration = stats.endTime - stats.startTime;
          collector.parseAll(); // This calculates stats
          onComplete(stats);
        }
      });

      (response.data as any).on('end', () => {
        onComplete(stats);
      });

      (response.data as any).on('error', (error: Error) => {
        if (error.message?.includes('aborted')) {
          onComplete(stats);
        } else {
          onError(error);
        }
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
    // Similar implementation to streamAgent
    try {
      const formData = new FormData();
      formData.append('message', request.message);
      formData.append('stream', 'true');
      formData.append('monitor', 'true');
      if (request.session_id) formData.append('session_id', request.session_id);
      if (request.user_id) formData.append('user_id', request.user_id);

      const url = `${this.baseUrl}/playground/teams/${request.team_id}/runs`;
      const response = await gaxiosRequest({
        url,
        method: 'POST',
        data: formData,
        responseType: 'stream',
        timeout: 0,
        signal: abortSignal,
      });

      const collector = this.createRawCollector();
      const { stats } = collector;
      let sessionId = request.session_id;

      // Handle streaming data - just collect raw data and extract content
      (response.data as any).on('data', (chunk: Buffer) => {
        collector.collectChunk(chunk.toString());
        
        // Fast content extraction 
        const chunkStr = chunk.toString();
        
        // Simple search for content events - look for both RunResponseContent and TeamRunResponseContent
        if (chunkStr.includes('ResponseContent')) {
          const lines = chunkStr.split('\n');
          for (const line of lines) {
            if ((line.includes('RunResponseContent') || line.includes('TeamRunResponseContent')) && line.includes('"content_type":"str"')) {
              try {
                const event = JSON.parse(line);
                // Extract from both thinking and content fields
                const textContent = event.thinking || event.content;
                if (textContent) {
                  onMessage({
                    content: textContent,
                    done: false,
                    session_id: sessionId,
                    metadata: { type: 'content' }
                  });
                }
              } catch (e) {
                // Try regex fallback for both thinking and content
                const thinkingMatch = line.match(/"thinking":"([^"]*)"/);
                const contentMatch = line.match(/"content":"([^"]*)"/);
                const extractedText = thinkingMatch?.[1] || contentMatch?.[1];
                if (extractedText) {
                  onMessage({
                    content: extractedText,
                    done: false,
                    session_id: sessionId,
                    metadata: { type: 'content' }
                  });
                }
              }
            }
          }
        }
        
        // Check for completion and post-process stats
        if (chunkStr.includes('"event":"TeamRunCompleted"') || chunkStr.includes('"event":"RunCompleted"')) {
          stats.endTime = Date.now();
          stats.totalDuration = stats.endTime - stats.startTime;
          collector.parseAll(); // This calculates stats
          onComplete(stats);
        }
      });

      (response.data as any).on('end', () => {
        onComplete(stats);
      });

      (response.data as any).on('error', (error: Error) => {
        if (error.message?.includes('aborted')) {
          onComplete(stats);
        } else {
          onError(error);
        }
      });

    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown streaming error'));
    }
  }

  // Reuse methods from localClient for non-streaming operations
  async listAgents(): Promise<LocalAPIResponse<any[]>> {
    const url = `${this.baseUrl}/playground/agents`;
    const response = await gaxiosRequest({
      url,
      method: 'GET',
      timeout: 5000,
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

export const streamingAPIClient = new StreamingAPIClient();

// Enhanced stats formatter with all metrics
export function formatRunStats(stats: RunStats): string {
  if (!stats) return '';
  
  const duration = stats.totalDuration ? (stats.totalDuration / 1000).toFixed(2) + 's' : 'N/A';
  
  return `\n📊 ${duration} | 🤖${stats.agentCalls} | 🔧${stats.toolCalls} | 🧠${stats.memoryUpdates} | 🔍${stats.ragQueries}`;
}