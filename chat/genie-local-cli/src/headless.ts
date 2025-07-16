import { localAPIClient } from './config/localClient.js';
import { appConfig } from './config/settings.js';

interface HeadlessOptions {
  prompt: string;
  target: string;
  sessionId?: string;
  output: 'json' | 'text' | 'markdown';
}

interface HeadlessResult {
  success: boolean;
  content?: string;
  error?: string;
  stats?: any;
  sessionId?: string;
}

export async function runHeadless(options: HeadlessOptions): Promise<HeadlessResult> {
  const { prompt, target, sessionId, output } = options;
  
  try {
    // Check API health first
    const healthResponse = await localAPIClient.healthCheck();
    if (!healthResponse.data) {
      return {
        success: false,
        error: `Cannot connect to API at ${appConfig.apiBaseUrl}. Please start the server with: cd /path/to/genie-agents && make dev`
      };
    }

    // Get available targets
    const [agentsResponse, teamsResponse, workflowsResponse] = await Promise.all([
      localAPIClient.listAgents(),
      localAPIClient.listTeams(),
      localAPIClient.listWorkflows(),
    ]);

    const allTargets = [
      ...(agentsResponse.data || []).map((a: any) => ({ ...a, type: 'agent' })),
      ...(teamsResponse.data || []).map((t: any) => ({ ...t, type: 'team' })),
      ...(workflowsResponse.data || []).map((w: any) => ({ ...w, type: 'workflow' })),
    ];

    // Find target by ID or name
    const targetStr = String(target).toLowerCase();
    const targetObj = allTargets.find((t: any) => 
      t.id === target || 
      t.name?.toLowerCase().includes(targetStr) ||
      t.team_id === target ||
      t.agent_id === target
    );

    if (!targetObj) {
      const availableTargets = allTargets.map((t: any) => `${t.type}:${t.id} (${t.name})`).join(', ');
      return {
        success: false,
        error: `Target "${target}" not found. Available targets: ${availableTargets}`
      };
    }

    // Generate session ID if not provided
    const finalSessionId = sessionId || `headless-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Execute based on target type using non-streaming API
    const startTime = Date.now();
    let response: any;
    
    if (targetObj.type === 'agent') {
      response = await localAPIClient.invokeAgent({
        agent_id: targetObj.id || targetObj.agent_id,
        message: prompt,
        session_id: finalSessionId,
      });
    } else if (targetObj.type === 'team') {
      response = await localAPIClient.invokeTeam({
        team_id: targetObj.id || targetObj.team_id,
        message: prompt,
        session_id: finalSessionId,
      });
    } else {
      response = await localAPIClient.executeWorkflow({
        workflow_id: targetObj.id || targetObj.workflow_id,
        params: { message: prompt },
        session_id: finalSessionId,
      });
    }

    if (response.error) {
      return {
        success: false,
        error: response.error
      };
    }

    const result = response.data?.content || 'No response content';
    const stats = response.data?.metrics || null;
    
    // Calculate actual elapsed time
    const endTime = Date.now();
    const actualDuration = (endTime - startTime) / 1000;
    
    // Override stats with actual timing
    if (stats) {
      stats.actual_time = actualDuration;
      stats.time = [actualDuration];
    }

    return {
      success: true,
      content: result,
      stats: stats,
      sessionId: finalSessionId
    };

  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
}

export function formatHeadlessOutput(result: HeadlessResult, format: 'json' | 'text' | 'markdown'): string {
  switch (format) {
    case 'json':
      return JSON.stringify(result, null, 2);
    
    case 'markdown':
      if (!result.success) {
        return `# Error\n\n${result.error}`;
      }
      
      let markdown = `# Response\n\n${result.content}\n\n`;
      
      if (result.stats) {
        markdown += `## Statistics\n\n`;
        const timeValue = result.stats.actual_time || (Array.isArray(result.stats.time) ? result.stats.time[0] : result.stats.time);
        markdown += `- **Total Time**: ${timeValue ? timeValue.toFixed(2) + 's' : 'N/A'}\n`;
        markdown += `- **Input Tokens**: ${result.stats.input_tokens || 0}\n`;
        markdown += `- **Output Tokens**: ${result.stats.output_tokens || 0}\n`;
        markdown += `- **Total Tokens**: ${result.stats.total_tokens || 0}\n`;
        markdown += `- **Session ID**: ${result.sessionId}\n`;
      }
      
      return markdown;
    
    case 'text':
    default:
      if (!result.success) {
        return `❌ Error: ${result.error}`;
      }
      
      let output = result.content || '';
      
      if (result.stats) {
        // Use actual measured time if available
        const timeValue = result.stats.actual_time || (Array.isArray(result.stats.time) ? result.stats.time[0] : result.stats.time);
        const time = timeValue ? timeValue.toFixed(2) + 's' : 'N/A';
        const tokens = result.stats.total_tokens || 0;
        const inputTokens = result.stats.input_tokens || 0;
        const outputTokens = result.stats.output_tokens || 0;
        output += `\n\n📊 Stats: ${time} | ${tokens} tokens (${inputTokens}↑ ${outputTokens}↓)`;
      }
      
      return output;
  }
}