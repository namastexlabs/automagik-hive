/**
 * Footer component adapted from gemini-cli for genie context
 */

import React from 'react';
import { Box, Text } from 'ink';
import { Colors } from '../colors.js';
import { shortenPath, tildeifyPath } from '../utils/textUtils.js';
import Gradient from 'ink-gradient';

interface FooterProps {
  model?: string;
  targetDir?: string;
  debugMode: boolean;
  debugMessage: string;
  sessionId: string;
  apiUrl: string;
  branchName?: string;
  nightly?: boolean;
  selectedTarget?: {
    type: 'agent' | 'team' | 'workflow';
    id: string;
    name: string;
  };
}

export const Footer: React.FC<FooterProps> = ({
  model,
  targetDir,
  debugMode,
  debugMessage,
  sessionId,
  apiUrl,
  branchName,
  nightly = false,
  selectedTarget,
}) => {
  const formatSessionId = (id: string): string => {
    return id.slice(-8); // Show last 8 characters
  };

  return (
    <Box marginTop={1} justifyContent="space-between" width="100%">
      <Box>
        {targetDir ? (
          nightly ? (
            <Gradient colors={Colors.GradientColors}>
              <Text>
                {shortenPath(tildeifyPath(targetDir), 70)}
                {branchName && <Text> ({branchName}*)</Text>}
              </Text>
            </Gradient>
          ) : (
            <Text color={Colors.LightBlue}>
              {shortenPath(tildeifyPath(targetDir), 70)}
              {branchName && <Text color={Colors.Gray}> ({branchName}*)</Text>}
            </Text>
          )
        ) : (
          <Text color={Colors.LightBlue}>
            Session: {formatSessionId(sessionId)}
          </Text>
        )}
        {debugMode && (
          <Text color={Colors.AccentRed}>
            {' ' + (debugMessage || '--debug')}
          </Text>
        )}
      </Box>

      {/* Middle Section: Genie Target Info */}
      <Box
        flexGrow={1}
        alignItems="center"
        justifyContent="center"
        display="flex"
      >
        {selectedTarget ? (
          <Text color={Colors.AccentPurple}>
            🎯 {selectedTarget.name} <Text color={Colors.Gray}>({selectedTarget.type})</Text>
          </Text>
        ) : (
          <Text color={Colors.AccentYellow}>
            🎯 genie-local-cli
          </Text>
        )}
      </Box>

      {/* Right Section: Model/API Info */}
      <Box alignItems="center">
        {model ? (
          <Text color={Colors.AccentBlue}>
            {model}
          </Text>
        ) : (
          <Text color={Colors.AccentBlue}>
            API: {apiUrl.replace(/^https?:\/\//, '')}
          </Text>
        )}
      </Box>
    </Box>
  );
};