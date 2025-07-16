import React from 'react';
import { Box, Text } from 'ink';
import { RadioButtonSelect } from './RadioButtonSelect.js';

interface TargetTypeDialogProps {
  onSelect: (targetType: 'agent' | 'team' | 'workflow') => void;
  availableTargets: {
    agents: any[];
    teams: any[];
    workflows: any[];
  };
}

export function TargetTypeDialog({
  onSelect,
  availableTargets,
}: TargetTypeDialogProps): React.JSX.Element {
  const items = [
    {
      label: `Agents (${availableTargets.agents.length} available)`,
      value: 'agent' as const,
      disabled: availableTargets.agents.length === 0,
    },
    {
      label: `Teams (${availableTargets.teams.length} available)`,
      value: 'team' as const,
      disabled: availableTargets.teams.length === 0,
    },
    {
      label: `Workflows (${availableTargets.workflows.length} available)`,
      value: 'workflow' as const,
      disabled: availableTargets.workflows.length === 0,
    },
  ];

  const handleSelect = (targetType: 'agent' | 'team' | 'workflow') => {
    onSelect(targetType);
  };

  return (
    <Box
      borderStyle="round"
      borderColor="#666666"
      flexDirection="column"
      padding={1}
      width="100%"
    >
      <Text bold>🧞 Welcome to Genie Local CLI</Text>
      <Box marginTop={1}>
        <Text>What would you like to interact with?</Text>
      </Box>
      <Box marginTop={1}>
        <RadioButtonSelect
          items={items}
          initialIndex={0}
          onSelect={handleSelect}
          isFocused={true}
        />
      </Box>
      <Box marginTop={1}>
        <Text color="#666666">(Use ↑/↓ arrows and Enter to select)</Text>
      </Box>
    </Box>
  );
}