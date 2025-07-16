import { useCallback, useState, useRef } from 'react';
import { StreamingState, MessageType, HistoryItem, APITarget } from '../types.js';
import { useStreamingContext } from '../contexts/StreamingContext.js';
import { StreamingResponse } from '../../config/localClient.js';
import { localAPIClient } from '../../config/localClient.js';
import { appConfig } from '../../config/settings.js';

interface UseLocalAPIStreamResult {
  streamingState: StreamingState;
  submitQuery: (message: string) => Promise<void>;
  cancelStream: () => void;
  initError: string | null;
  pendingMessage: HistoryItem | null;
}

export const useLocalAPIStream = (
  addMessage: (message: Omit<HistoryItem, 'id'>) => void,
  selectedTarget: APITarget | null,
  sessionId: string,
  setDebugMessage: (message: string) => void
): UseLocalAPIStreamResult => {
  const { streamingState, setStreamingState } = useStreamingContext();
  const [initError, setInitError] = useState<string | null>(null);
  const [pendingMessage, setPendingMessage] = useState<HistoryItem | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentStreamRef = useRef<string>('');

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    // Reset state
    setPendingMessage(null);
    setStreamingState(StreamingState.Idle);
    setDebugMessage('Stream canceled by user');
    currentStreamRef.current = '';
    
    // Add cancellation message
    addMessage({
      type: MessageType.ERROR,
      text: 'Request canceled by user',
      timestamp: Date.now(),
      sessionId,
    });
  }, [setStreamingState, setDebugMessage, addMessage, sessionId]);

  const submitQuery = useCallback(async (message: string) => {
    if (!selectedTarget) {
      setInitError('No target selected');
      return;
    }

    if (streamingState !== StreamingState.Idle) {
      return; // Already processing
    }

    // Reset state
    setInitError(null);
    setPendingMessage(null);
    currentStreamRef.current = '';

    // Add user message
    const userMessage: Omit<HistoryItem, 'id'> = {
      type: MessageType.USER,
      text: message,
      timestamp: Date.now(),
      sessionId,
      metadata: {
        target: selectedTarget,
      },
    };
    addMessage(userMessage);

    // Create pending assistant message
    const pendingAssistantMessage: HistoryItem = {
      id: Date.now() + Math.random(), // More unique temporary ID
      type: MessageType.ASSISTANT,
      text: '',
      timestamp: Date.now(),
      sessionId,
      metadata: {
        target: selectedTarget,
        streaming: true,
        complete: false,
      },
    };
    setPendingMessage(pendingAssistantMessage);

    try {
      setStreamingState(StreamingState.Connecting);
      setDebugMessage(`Connecting to ${selectedTarget.type} ${selectedTarget.id}...`);

      // Create abort controller for this request
      abortControllerRef.current = new AbortController();

      setStreamingState(StreamingState.Responding);
      setDebugMessage(`Streaming response from ${selectedTarget.type} ${selectedTarget.id}...`);

      // Handle streaming response
      const handleStreamingMessage = (data: StreamingResponse) => {
        // Determine message type based on metadata
        let messageType = MessageType.ASSISTANT;
        if (data.metadata?.type === 'thinking') {
          messageType = MessageType.THINKING;
        } else if (data.metadata?.type === 'tool_start') {
          messageType = MessageType.TOOL_START;
        } else if (data.metadata?.type === 'tool_complete') {
          messageType = MessageType.TOOL_COMPLETE;
        } else if (data.metadata?.type === 'agent_start') {
          messageType = MessageType.AGENT_START;
        } else if (data.metadata?.type === 'team_start') {
          messageType = MessageType.TEAM_START;
        } else if (data.metadata?.type === 'memory_update') {
          messageType = MessageType.MEMORY_UPDATE;
        } else if (data.metadata?.type === 'rag_query') {
          messageType = MessageType.INFO;
        }

        // For content messages, accumulate in current stream
        if (data.metadata?.type === 'content' || !data.metadata?.type) {
          currentStreamRef.current += data.content;
          
          setPendingMessage(prev => prev ? {
            ...prev,
            text: currentStreamRef.current,
            metadata: {
              ...prev.metadata,
              complete: data.done,
            },
          } : null);
        } else {
          // For other message types, add as separate messages immediately with rich metadata
          const immediateMessage: Omit<HistoryItem, 'id'> = {
            type: messageType,
            text: data.content,
            timestamp: Date.now(),
            sessionId: data.session_id || sessionId,
            metadata: {
              target: selectedTarget,
              streaming: false,
              complete: true,
              event: data.metadata?.event,
              eventId: data.metadata?.eventId || `${messageType}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              // Pass through all the rich metadata from the API
              tool: data.metadata?.tool,
              agent: data.metadata?.agent,
              team: data.metadata?.team,
              memory: data.metadata?.memory,
              thinking: data.metadata?.thinking,
              rag: data.metadata?.rag,
            },
          };
          addMessage(immediateMessage);
        }

        if (data.done) {
          // Finalize the main content message if it exists
          if (currentStreamRef.current.trim()) {
            const finalMessage: Omit<HistoryItem, 'id'> = {
              type: MessageType.ASSISTANT,
              text: currentStreamRef.current,
              timestamp: Date.now(),
              sessionId: data.session_id || sessionId,
              metadata: {
                target: selectedTarget,
                streaming: false,
                complete: true,
              },
            };
            
            addMessage(finalMessage);
          }
          
          setPendingMessage(null);
          setStreamingState(StreamingState.Idle);
          setDebugMessage('');
          currentStreamRef.current = '';
        }
      };

      const handleStreamingError = (error: Error) => {
        console.error('Streaming error:', error);
        
        // Graceful error handling based on error type
        let userFriendlyMessage = '';
        let actionableAdvice = '';
        
        if (error.message.includes('ECONNREFUSED') || error.message.includes('connect')) {
          userFriendlyMessage = '🔌 Cannot connect to Genie API server';
          actionableAdvice = `
💡 **Quick Fix:**
   • Check if the API server is running: \`curl ${appConfig.apiBaseUrl}/api/v1/health\`
   • Start the server: \`cd /path/to/genie-agents && make dev\`
   • Or change API_BASE_URL in .env to correct server address

🔧 **Troubleshooting:**
   • Server might be starting up (wait 30 seconds)
   • Wrong port/host in configuration
   • Firewall blocking connection`;
        } else if (error.message.includes('timeout')) {
          userFriendlyMessage = '⏱️ Request timed out';
          actionableAdvice = `
💡 **Solutions:**
   • Server may be overloaded, try again in a moment
   • Check network connectivity
   • Increase timeout in settings if needed`;
        } else if (error.message.includes('404') || error.message.includes('Not Found')) {
          userFriendlyMessage = '🔍 API endpoint not found';
          actionableAdvice = `
💡 **Check:**
   • API server version compatibility
   • Endpoint URL configuration
   • Server running the correct version`;
        } else {
          userFriendlyMessage = `❌ ${error.message}`;
          actionableAdvice = `
💡 **General troubleshooting:**
   • Check server logs for detailed error information
   • Verify API server is healthy: \`curl ${appConfig.apiBaseUrl}/api/v1/health\`
   • Contact support if issue persists`;
        }
        
        setInitError(userFriendlyMessage);
        setPendingMessage(null);
        setStreamingState(StreamingState.Error);
        setDebugMessage(userFriendlyMessage);
        
        // Add graceful error message
        addMessage({
          type: MessageType.ERROR,
          text: userFriendlyMessage + actionableAdvice,
          timestamp: Date.now(),
          sessionId,
        });
      };

      const handleStreamingComplete = (stats?: any) => {
        setStreamingState(StreamingState.Idle);
        setDebugMessage('');
        
        // Display run statistics if available
        if (stats) {
          // Use actual measured time if available, otherwise fall back to API time
          const timeValue = stats.actual_time || (Array.isArray(stats.time) ? stats.time[0] : stats.time);
          const time = timeValue ? timeValue.toFixed(2) + 's' : 'N/A';
          const tokens = stats.total_tokens || 0;
          const inputTokens = stats.input_tokens || 0;
          const outputTokens = stats.output_tokens || 0;
          
          const statsMessage = `📊 Stats: ${time} | ${tokens} tokens (${inputTokens}↑ ${outputTokens}↓)`;
          
          addMessage({
            type: MessageType.INFO,
            text: statsMessage,
            timestamp: Date.now(),
            sessionId,
            metadata: {
              target: selectedTarget,
              isStats: true,
            },
          });
        }
      };

      // Track actual start time
      const actualStartTime = Date.now();
      
      // Execute based on target type using non-streaming API
      let response: any;
      
      switch (selectedTarget.type) {
        case 'agent':
          response = await localAPIClient.invokeAgent({
            agent_id: selectedTarget.id,
            message,
            session_id: sessionId,
          });
          break;

        case 'team':
          response = await localAPIClient.invokeTeam({
            team_id: selectedTarget.id,
            message,
            session_id: sessionId,
          });
          break;

        case 'workflow':
          response = await localAPIClient.executeWorkflow({
            workflow_id: selectedTarget.id,
            params: { message },
            session_id: sessionId,
          });
          break;

        default:
          throw new Error(`Unknown target type: ${selectedTarget.type}`);
      }
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      // Simulate streaming by showing intermediate steps, then complete response
      setDebugMessage(`Processing response...`);
      
      // Add a processing message
      handleStreamingMessage({
        content: '🔄 Processing your request...',
        done: false,
        session_id: response.session_id || sessionId,
        metadata: { type: 'agent_start' }
      });
      
      // Show processing step for a meaningful duration (2 seconds)
      setTimeout(() => {
        const content = response.data?.content || 'No response content';
        handleStreamingMessage({
          content,
          done: true,
          session_id: response.session_id || sessionId,
        });
        
        // Calculate actual elapsed time and fix stats
        const actualEndTime = Date.now();
        const actualDuration = (actualEndTime - actualStartTime) / 1000;
        
        // Handle completion with corrected stats
        setTimeout(() => {
          const stats = response.data?.metrics || null;
          if (stats) {
            // Override the API's timing with our actual measurement
            stats.actual_time = actualDuration;
            stats.time = [actualDuration]; // Override time array
          }
          handleStreamingComplete(stats);
        }, 100);
      }, 2000); // Show processing for 2 seconds

    } catch (error) {
      console.error('Submit query error:', error);
      
      // Graceful error handling (same logic as handleStreamingError)
      const errorObj = error instanceof Error ? error : new Error('Unknown error');
      let userFriendlyMessage = '';
      let actionableAdvice = '';
      
      if (errorObj.message.includes('ECONNREFUSED') || errorObj.message.includes('connect')) {
        userFriendlyMessage = '🔌 Cannot connect to Genie API server';
        actionableAdvice = `
💡 **Quick Fix:**
   • Check if the API server is running: \`curl ${appConfig.apiBaseUrl}/api/v1/health\`
   • Start the server: \`cd /path/to/genie-agents && make dev\`
   • Or change API_BASE_URL in .env to correct server address

🔧 **Troubleshooting:**
   • Server might be starting up (wait 30 seconds)
   • Wrong port/host in configuration
   • Firewall blocking connection`;
      } else if (errorObj.message.includes('timeout')) {
        userFriendlyMessage = '⏱️ Request timed out';
        actionableAdvice = `
💡 **Solutions:**
   • Server may be overloaded, try again in a moment
   • Check network connectivity
   • Increase timeout in settings if needed`;
      } else if (errorObj.message.includes('404') || errorObj.message.includes('Not Found')) {
        userFriendlyMessage = '🔍 API endpoint not found';
        actionableAdvice = `
💡 **Check:**
   • API server version compatibility
   • Endpoint URL configuration
   • Server running the correct version`;
      } else {
        userFriendlyMessage = `❌ ${errorObj.message}`;
        actionableAdvice = `
💡 **General troubleshooting:**
   • Check server logs for detailed error information
   • Verify API server is healthy: \`curl ${appConfig.apiBaseUrl}/api/v1/health\`
   • Contact support if issue persists`;
      }
      
      setInitError(userFriendlyMessage);
      setPendingMessage(null);
      setStreamingState(StreamingState.Error);
      setDebugMessage(userFriendlyMessage);
      
      // Add graceful error message
      addMessage({
        type: MessageType.ERROR,
        text: userFriendlyMessage + actionableAdvice,
        timestamp: Date.now(),
        sessionId,
      });
    }
  }, [
    selectedTarget,
    sessionId,
    streamingState,
    setStreamingState,
    addMessage,
    setDebugMessage,
  ]);

  return {
    streamingState,
    submitQuery,
    cancelStream,
    initError,
    pendingMessage,
  };
};