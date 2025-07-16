import React from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import { StreamingState } from '../types.js';
import { appConfig } from '../../config/settings.js';

interface LoadingIndicatorProps {
  currentLoadingPhrase: string;
  elapsedTime: number;
  streamingState: StreamingState;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  currentLoadingPhrase,
  elapsedTime,
  streamingState,
}) => {
  const isLoading = streamingState === StreamingState.Connecting || 
                   streamingState === StreamingState.Waiting ||
                   streamingState === StreamingState.Responding;

  const isStreaming = streamingState === StreamingState.Responding;

  if (!isLoading) {
    return null;
  }

  const formatElapsedTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    return `${seconds}s`;
  };

  const getStreamingStateText = (): string => {
    switch (streamingState) {
      case StreamingState.Connecting:
        return 'Connecting to API...';
      case StreamingState.Waiting:
        return 'Waiting for response...';
      case StreamingState.Responding:
        return 'Receiving response...';
      default:
        return currentLoadingPhrase;
    }
  };

  return (
    <Box marginY={1}>
      <Box alignItems="center">
        {appConfig.enableSpinner && (
          <>
            <Spinner type="dots" />
            <Text> </Text>
          </>
        )}
        <Text color={isStreaming ? 'green' : 'yellow'}>
          {getStreamingStateText()}
        </Text>
        {elapsedTime > 0 && (
          <Text color="gray"> ({formatElapsedTime(elapsedTime)})</Text>
        )}
      </Box>
    </Box>
  );
};