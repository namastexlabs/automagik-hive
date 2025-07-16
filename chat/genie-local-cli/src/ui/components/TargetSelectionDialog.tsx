import React from 'react';
import { Box, Text, useInput } from 'ink';
import { RadioButtonSelect } from './RadioButtonSelect.js';
import { Colors } from '../colors.js';

interface TargetSelectionDialogProps {
  targetType: 'agent' | 'team' | 'workflow';
  targets: any[];
  onSelect: (target: { type: 'agent' | 'team' | 'workflow'; id: string; name: string }) => void;
  onBack: () => void;
}

export function TargetSelectionDialog({
  targetType,
  targets,
  onSelect,
  onBack,
}: TargetSelectionDialogProps): React.JSX.Element {
  const items = targets.map((target) => ({
    label: target.name || target.agent_id || target.team_id || target.workflow_id || 'Unknown',
    value: target,
  }));

  const handleSelect = (target: any) => {
    const id = target.agent_id || target.team_id || target.workflow_id;
    const name = target.name || id || 'Unknown';
    onSelect({
      type: targetType,
      id,
      name,
    });
  };

  useInput((input, key) => {
    if (key.escape) {
      onBack();
    }
  });

  const targetTypeDisplay = targetType.charAt(0).toUpperCase() + targetType.slice(1);

  return (
    <Box
      borderStyle="round"
      borderColor={Colors.AccentPurple}
      flexDirection="column"
      padding={1}
      width="100%"
    >
      <Text bold color={Colors.AccentPurple}>Select {targetTypeDisplay}</Text>
      <Box marginTop={1}>
        <Text color={Colors.Foreground}>Choose which {targetType} you want to interact with:</Text>
      </Box>
      <Box marginTop={1}>
        <RadioButtonSelect
          items={items}
          initialIndex={0}
          onSelect={handleSelect}
          isFocused={true}
          showScrollArrows={items.length > 10}
          maxItemsToShow={10}
        />
      </Box>
      <Box marginTop={1}>
        <Text color={Colors.Gray}>(Use ↑/↓ arrows and Enter to select, Esc to go back)</Text>
      </Box>
    </Box>
  );
}