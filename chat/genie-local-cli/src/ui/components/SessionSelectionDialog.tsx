import React from 'react';
import { Box, Text, useInput } from 'ink';
import { RadioButtonSelect } from './RadioButtonSelect.js';

interface SessionSelectionDialogProps {
  selectedTarget: { type: 'agent' | 'team' | 'workflow'; id: string; name: string };
  onSelect: (sessionAction: 'new' | 'existing') => void;
  onBack: () => void;
}

export function SessionSelectionDialog({
  selectedTarget,
  onSelect,
  onBack,
}: SessionSelectionDialogProps): React.JSX.Element {
  const items = [
    {
      label: 'Start new conversation',
      value: 'new' as const,
    },
    {
      label: 'Continue existing session (coming soon)',
      value: 'existing' as const,
      disabled: true,
    },
  ];

  const handleSelect = (sessionAction: 'new' | 'existing') => {
    onSelect(sessionAction);
  };

  useInput((input, key) => {
    if (key.escape) {
      onBack();
    }
  });

  return (
    <Box
      borderStyle="round"
      borderColor="#666666"
      flexDirection="column"
      padding={1}
      width="100%"
    >
      <Text bold>Session Options</Text>
      <Box marginTop={1}>
        <Text>Ready to chat with: <Text color="#00ff00">{selectedTarget.name}</Text></Text>
      </Box>
      <Box marginTop={1}>
        <Text>How would you like to proceed?</Text>
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
        <Text color="#666666">(Use ↑/↓ arrows and Enter to select, Esc to go back)</Text>
      </Box>
    </Box>
  );
}