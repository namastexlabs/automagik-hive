/**
 * Loading indicator adapted from gemini-cli for genie context
 */

import React from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import { StreamingState } from '../types.js';
import { Colors } from '../colors.js';

interface LoadingIndicatorProps {
  currentLoadingPhrase?: string;
  elapsedTime: number;
  thought?: string;
  streamingState?: StreamingState;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  currentLoadingPhrase,
  elapsedTime,
  thought,
  streamingState,
}) => {
  // Show loading if we have a current phrase or if we're not idle
  const isLoading = streamingState !== StreamingState.Idle && (
    currentLoadingPhrase || 
    streamingState === StreamingState.Connecting || 
    streamingState === StreamingState.Waiting ||
    streamingState === StreamingState.Responding
  );

  const isStreaming = streamingState === StreamingState.Responding;

  if (!isLoading && !thought) {
    return null;
  }

  const formatElapsedTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    return `${seconds}s`;
  };

  const getStreamingStateText = (): string => {
    if (currentLoadingPhrase) {
      return currentLoadingPhrase;
    }
    
    switch (streamingState) {
      case StreamingState.Connecting:
        return '🧞 Connecting to genie...';
      case StreamingState.Waiting:
        return '🧞 Waiting for response...';
      case StreamingState.Responding:
        return '🧞 Receiving response...';
      default:
        return '🧞 Thinking...';
    }
  };

  return (
    <Box marginY={1} flexDirection="column">
      {/* Thought display (if available) */}
      {thought && (
        <Box marginBottom={1}>
          <Text color={Colors.Comment} italic>
            💭 {thought}
          </Text>
        </Box>
      )}

      {/* Loading indicator */}
      {isLoading && (
        <Box alignItems="center">
          <Spinner type="dots" />
          <Text> </Text>
          <Text color={isStreaming ? Colors.AccentGreen : Colors.AccentYellow}>
            {getStreamingStateText()}
          </Text>
          {elapsedTime > 0 && (
            <Text color={Colors.Gray}> ({formatElapsedTime(elapsedTime)})</Text>
          )}
        </Box>
      )}
    </Box>
  );
};