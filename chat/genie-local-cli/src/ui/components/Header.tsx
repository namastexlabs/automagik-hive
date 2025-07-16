import React from 'react';
import { Box, Text } from 'ink';
import SelectInput from 'ink-select-input';

interface HeaderProps {
  terminalWidth: number;
  version: string;
  connectionStatus: 'connecting' | 'connected' | 'error';
  selectedTarget: { type: 'agent' | 'team' | 'workflow'; id: string; name: string } | null;
  availableTargets: {
    agents: any[];
    teams: any[];
    workflows: any[];
  };
  onTargetChange: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  terminalWidth,
  version,
  connectionStatus,
  selectedTarget,
  availableTargets,
  onTargetChange,
}) => {
  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'green';
      case 'connecting': return 'yellow';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return '● Connected';
      case 'connecting': return '○ Connecting...';
      case 'error': return '✗ Connection Error';
      default: return '○ Unknown';
    }
  };

  const formatTargetDisplay = () => {
    if (!selectedTarget) {
      return 'No target selected';
    }
    return `${selectedTarget.type.toUpperCase()}: ${selectedTarget.name}`;
  };

  return (
    <Box flexDirection="column" marginBottom={1}>
      {/* Title and version with gemini-style border */}
      <Box 
        borderStyle="round" 
        borderColor="blue" 
        paddingX={1} 
        marginBottom={1}
        justifyContent="space-between"
      >
        <Box>
          <Text bold color="cyan">🧞 Genie Local CLI</Text>
          <Text color="gray"> v{version}</Text>
        </Box>
        <Text color={getConnectionStatusColor()}>
          {getConnectionStatusText()}
        </Text>
      </Box>

      {/* Target selection display */}
      <Box marginTop={1} marginBottom={1}>
        <Box flexDirection="column">
          <Text color="cyan">Current Target: </Text>
          <Text bold>{formatTargetDisplay()}</Text>
          
          {connectionStatus === 'connected' && (
            <Box marginTop={1}>
              <Text color="gray">
                Available: {availableTargets.agents.length} agents, {availableTargets.teams.length} teams, {availableTargets.workflows.length} workflows
              </Text>
            </Box>
          )}
        </Box>
      </Box>

      {/* Separator */}
      <Box>
        <Text color="gray">{'─'.repeat(Math.min(terminalWidth, 80))}</Text>
      </Box>
    </Box>
  );
};