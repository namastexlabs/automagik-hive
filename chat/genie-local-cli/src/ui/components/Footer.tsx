import React from 'react';
import { Box, Text } from 'ink';

interface FooterProps {
  debugMode: boolean;
  debugMessage: string;
  sessionId: string;
  apiUrl: string;
}

export const Footer: React.FC<FooterProps> = ({
  debugMode,
  debugMessage,
  sessionId,
  apiUrl,
}) => {
  const formatSessionId = (id: string): string => {
    return id.slice(-8); // Show last 8 characters
  };

  return (
    <Box flexDirection="column" marginTop={1}>
      {/* Debug message */}
      {debugMode && debugMessage && (
        <Box marginBottom={1}>
          <Text color="gray" italic>
            Debug: {debugMessage}
          </Text>
        </Box>
      )}

      {/* Footer info */}
      <Box justifyContent="space-between">
        <Box>
          <Text color="gray">
            Session: {formatSessionId(sessionId)}
          </Text>
        </Box>
        <Box>
          <Text color="gray">
            API: {apiUrl}
          </Text>
        </Box>
      </Box>

      {/* Additional debug info */}
      {debugMode && (
        <Box marginTop={1}>
          <Text color="gray" dimColor>
            Debug mode enabled • Full session ID: {sessionId}
          </Text>
        </Box>
      )}
    </Box>
  );
};