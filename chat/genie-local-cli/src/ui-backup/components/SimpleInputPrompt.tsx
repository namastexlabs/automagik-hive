import React, { useState, useCallback } from 'react';
import { Box, Text } from 'ink';
import TextInput from 'ink-text-input';

interface SimpleInputPromptProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const SimpleInputPrompt: React.FC<SimpleInputPromptProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'Type your message...',
}) => {
  const [input, setInput] = useState<string>('');

  const handleSubmit = useCallback((value: string) => {
    if (value.trim() && !disabled) {
      onSubmit(value.trim());
      setInput('');
    }
  }, [onSubmit, disabled]);

  const handleChange = useCallback((value: string) => {
    setInput(value);
  }, []);

  return (
    <Box flexDirection="column" marginY={1}>
      <Box>
        <Text color="cyan">{'> '}</Text>
        <TextInput
          value={input}
          placeholder={placeholder}
          onChange={handleChange}
          onSubmit={handleSubmit}
          focus={!disabled}
          showCursor={!disabled}
        />
      </Box>
      
      {!disabled && (
        <Box marginTop={1}>
          <Text color="gray">
            Press Enter to send • Ctrl+C to exit
          </Text>
        </Box>
      )}
    </Box>
  );
};