import React, { useState, useCallback, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import TextInput from 'ink-text-input';

interface LibraryInputPromptProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const LibraryInputPrompt: React.FC<LibraryInputPromptProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'Type your message...',
}) => {
  const [input, setInput] = useState<string>('');
  const [isMultiline, setIsMultiline] = useState<boolean>(false);

  // Auto-detect multiline content
  useEffect(() => {
    setIsMultiline(input.includes('\n') || input.length > 100);
  }, [input]);

  const handleSubmit = useCallback((value: string) => {
    if (value.trim() && !disabled) {
      onSubmit(value.trim());
      setInput('');
      setIsMultiline(false);
    }
  }, [onSubmit, disabled]);

  const handleChange = useCallback((value: string) => {
    setInput(value);
  }, []);

  // Handle paste events - automatically enable multiline for large content
  const handleKeyPress = useCallback((value: string) => {
    // This is a workaround for detecting large paste operations
    if (value.length > input.length + 50) {
      setIsMultiline(true);
    }
  }, [input.length]);

  const lines = input.split('\n');
  const displayLines = lines.slice(0, 8); // Max 8 lines visible

  if (isMultiline && lines.length > 1) {
    return (
      <Box flexDirection="column" marginY={1}>
        <Box flexDirection="column" borderStyle="round" borderColor="cyan" paddingX={1}>
          <Text color="cyan">Multiline input ({lines.length} lines, {input.length} chars)</Text>
          {displayLines.map((line, index) => (
            <Text key={index}>{line || ' '}</Text>
          ))}
          {lines.length > 8 && (
            <Text color="gray">... {lines.length - 8} more lines</Text>
          )}
        </Box>
        <Box marginTop={1}>
          <Text color="gray">
            Paste your content and press Ctrl+Enter to send, or type normally
          </Text>
        </Box>
      </Box>
    );
  }

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
          highlightPastedText={true}
        />
      </Box>
      
      {!disabled && (
        <Box marginTop={1}>
          <Text color="gray">
            Type your message • Enter to send • Large content becomes multiline automatically
          </Text>
        </Box>
      )}
    </Box>
  );
};