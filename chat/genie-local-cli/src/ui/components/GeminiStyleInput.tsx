/**
 * Gemini-style input component that combines gemini's visual design
 * with our working genie backend functionality
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import TextInput from 'ink-text-input';
import { Colors } from '../colors.js';

interface GeminiStyleInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  focus?: boolean;
}

export const GeminiStyleInput: React.FC<GeminiStyleInputProps> = ({
  onSubmit,
  disabled = false,
  placeholder = '  Type your message...',
  focus = true,
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

  // Handle Escape key to clear input
  useInput((inputChar, key) => {
    if (key.escape && focus && !disabled) {
      setInput('');
      setIsMultiline(false);
    }
  }, { isActive: focus && !disabled });

  const lines = input.split('\n');
  const displayLines = lines.slice(0, 8); // Max 8 lines visible

  // Show multiline view when content has newlines or is long
  if (isMultiline && lines.length > 1) {
    return (
      <Box flexDirection="column" marginY={1}>
        <Box
          borderStyle="round"
          borderColor={Colors.AccentPurple}
          paddingX={1}
          flexDirection="column"
        >
          <Box marginBottom={1}>
            <Text color="magenta">{'> '}</Text>
            <Text color="gray">
              Multiline input ({lines.length} lines, {input.length} chars)
            </Text>
          </Box>
          {displayLines.map((line, index) => (
            <Text key={index} color="white">
              {line || ' '}
            </Text>
          ))}
          {lines.length > 8 && (
            <Text color="gray">... {lines.length - 8} more lines</Text>
          )}
        </Box>
        <Box marginTop={1}>
          <Text color="gray">
            Enter: Send • Esc: Clear text • Paste content works automatically
          </Text>
        </Box>
      </Box>
    );
  }

  // Single line input with gemini styling
  return (
    <Box flexDirection="column" marginY={1}>
      <Box
        borderStyle="round"
        borderColor={Colors.AccentPurple}
        paddingX={1}
      >
        <Text color="magenta">{'> '}</Text>
        <Box flexGrow={1}>
          <TextInput
            value={input}
            placeholder={placeholder}
            onChange={handleChange}
            onSubmit={handleSubmit}
            focus={focus && !disabled}
            showCursor={focus && !disabled}
            highlightPastedText={true}
          />
        </Box>
      </Box>
      
      {focus && !disabled && (
        <Box marginTop={1}>
          <Text color="gray">
            Enter: Send • Esc: Clear text • Paste works • Large content becomes multiline automatically
          </Text>
        </Box>
      )}
    </Box>
  );
};