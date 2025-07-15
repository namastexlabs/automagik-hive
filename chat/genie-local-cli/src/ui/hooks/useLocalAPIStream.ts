import { useCallback, useState, useRef } from 'react';
import { StreamingState, MessageType, HistoryItem, APITarget } from '../types.js';
import { useStreamingContext } from '../contexts/StreamingContext.js';
import { localAPIClient, StreamingResponse } from '../../config/localClient.js';
import { appConfig } from '../../config/settings.js';

interface UseLocalAPIStreamResult {
  streamingState: StreamingState;
  submitQuery: (message: string) => Promise<void>;
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
        currentStreamRef.current += data.content;
        
        setPendingMessage(prev => prev ? {
          ...prev,
          text: currentStreamRef.current,
          metadata: {
            ...prev.metadata,
            complete: data.done,
          },
        } : null);

        if (data.done) {
          // Finalize the message
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
            handleStreamingComplete
          );
          break;

        case 'team':
          // For now, use non-streaming fallback for teams
          const teamResponse = await localAPIClient.invokeTeam({
            team_id: selectedTarget.id,
            message,
            session_id: sessionId,
          });
          
          if (teamResponse.error) {
            throw new Error(teamResponse.error);
          }
          
          // Simulate streaming for teams
          const teamContent = teamResponse.data?.content || 'No response from team';
          handleStreamingMessage({
            content: teamContent,
            done: true,
            session_id: teamResponse.session_id,
          });
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
    initError,
    pendingMessage,
  };
};