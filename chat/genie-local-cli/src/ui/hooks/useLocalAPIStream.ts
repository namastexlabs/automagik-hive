import { useCallback, useState, useRef } from 'react';
import { StreamingState, MessageType, HistoryItem, APITarget } from '../types.js';
import { useStreamingContext } from '../contexts/StreamingContext.js';
import { localAPIClient, StreamingResponse } from '../../config/localClient.js';
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
      id: Date.now(), // Temporary ID
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
              eventId: data.metadata?.eventId || `${messageType}-${Date.now()}-${Math.random()}`,
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
        setInitError(error.message);
        setPendingMessage(null);
        setStreamingState(StreamingState.Error);
        setDebugMessage(`Error: ${error.message}`);
        
        // Add error message
        addMessage({
          type: MessageType.ERROR,
          text: `Streaming error: ${error.message}`,
          timestamp: Date.now(),
          sessionId,
        });
      };

      const handleStreamingComplete = () => {
        setStreamingState(StreamingState.Idle);
        setDebugMessage('');
      };

      // Start streaming based on target type
      switch (selectedTarget.type) {
        case 'agent':
          await localAPIClient.streamAgent(
            {
              agent_id: selectedTarget.id,
              message,
              session_id: sessionId,
            },
            handleStreamingMessage,
            handleStreamingError,
            handleStreamingComplete,
            abortControllerRef.current?.signal
          );
          break;

        case 'team':
          await localAPIClient.streamTeam(
            {
              team_id: selectedTarget.id,
              message,
              session_id: sessionId,
            },
            handleStreamingMessage,
            handleStreamingError,
            handleStreamingComplete,
            abortControllerRef.current?.signal
          );
          break;

        case 'workflow':
          // For now, use non-streaming fallback for workflows
          const workflowResponse = await localAPIClient.executeWorkflow({
            workflow_id: selectedTarget.id,
            params: { message },
            session_id: sessionId,
          });
          
          if (workflowResponse.error) {
            throw new Error(workflowResponse.error);
          }
          
          // Simulate streaming for workflows
          const workflowContent = workflowResponse.data?.content || 'No response from workflow';
          handleStreamingMessage({
            content: workflowContent,
            done: true,
            session_id: workflowResponse.session_id,
          });
          break;

        default:
          throw new Error(`Unknown target type: ${selectedTarget.type}`);
      }

    } catch (error) {
      console.error('Submit query error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setInitError(errorMessage);
      setPendingMessage(null);
      setStreamingState(StreamingState.Error);
      setDebugMessage(`Error: ${errorMessage}`);
      
      // Add error message to history
      addMessage({
        type: MessageType.ERROR,
        text: `Failed to send message: ${errorMessage}`,
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