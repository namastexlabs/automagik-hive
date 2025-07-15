import React, { useState, useCallback } from 'react';
import { Box, Text, useInput } from 'ink';

interface InputPromptProps {
  onSubmit: (message: string) => void;
  inputWidth: number;
  disabled?: boolean;
  placeholder?: string;
}

export const InputPrompt: React.FC<InputPromptProps> = ({
  onSubmit,
  inputWidth,
  disabled = false,
  placeholder = 'Type your message...',
}) => {
  const [input, setInput] = useState<string>('');
  const [cursorPosition, setCursorPosition] = useState<number>(0);

  const handleSubmit = useCallback(() => {
    if (input.trim() && !disabled) {
      onSubmit(input.trim());
      setInput('');
      setCursorPosition(0);
    }
  }, [input, onSubmit, disabled]);

  useInput((inputChar, key) => {
    if (disabled) {
      return;
    }

    if (key.return) {
      handleSubmit();
    } else if (key.backspace || key.delete) {
      if (cursorPosition > 0) {
        const newInput = input.slice(0, cursorPosition - 1) + input.slice(cursorPosition);
        setInput(newInput);
        setCursorPosition(Math.max(0, cursorPosition - 1));
      }
    } else if (key.leftArrow) {
      setCursorPosition(Math.max(0, cursorPosition - 1));
    } else if (key.rightArrow) {
      setCursorPosition(Math.min(input.length, cursorPosition + 1));
    } else if (key.ctrl && inputChar === 'a') {
      setCursorPosition(0);
    } else if (key.ctrl && inputChar === 'e') {
      setCursorPosition(input.length);
    } else if (key.ctrl && inputChar === 'u') {
      setInput('');
      setCursorPosition(0);
    } else if (key.ctrl && inputChar === 'k') {
      setInput(input.slice(0, cursorPosition));
    } else if (inputChar && !key.ctrl && !key.meta) {
      const newInput = input.slice(0, cursorPosition) + inputChar + input.slice(cursorPosition);
      setInput(newInput);
      setCursorPosition(cursorPosition + 1);
    }
  });

  const displayText = input || placeholder;
  const isPlaceholder = !input;
  
  // Create visual cursor
  const beforeCursor = input.slice(0, cursorPosition);
  const atCursor = input[cursorPosition] || ' ';
  const afterCursor = input.slice(cursorPosition + 1);

  return (
    <Box flexDirection="column" marginY={1}>
      <Box>
        <Text color="cyan">{'> '}</Text>
        {disabled ? (
          <Text color="gray">{placeholder}</Text>
        ) : (
          <Box>
            {isPlaceholder ? (
              <Text color="gray">{placeholder}</Text>
            ) : (
              <>
                <Text>{beforeCursor}</Text>
                <Text inverse={true}>{atCursor}</Text>
                <Text>{afterCursor}</Text>
              </>
            )}
          </Box>
        )}
      </Box>
      
      {!disabled && (
        <Box marginTop={1}>
          <Text color="gray">
            Press Enter to send • Ctrl+H for help • Ctrl+L to clear • Ctrl+C to exit
          </Text>
        </Box>
      )}
    </Box>
  );
};