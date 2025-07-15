import React, { useState, useCallback } from 'react';
import { Box, Text, useInput } from 'ink';

interface BasicInputPromptProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const BasicInputPrompt: React.FC<BasicInputPromptProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'Type your message...',
}) => {
  const [input, setInput] = useState('');
  const [cursorPosition, setCursorPosition] = useState(0);

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
      if (key.shift) {
        // Shift+Enter adds newline
        const newInput = input.slice(0, cursorPosition) + '\n' + input.slice(cursorPosition);
        setInput(newInput);
        setCursorPosition(cursorPosition + 1);
      } else {
        // Regular Enter submits
        handleSubmit();
      }
    } else if (key.backspace) {
      if (cursorPosition > 0) {
        const newInput = input.slice(0, cursorPosition - 1) + input.slice(cursorPosition);
        setInput(newInput);
        setCursorPosition(cursorPosition - 1);
      }
    } else if (key.delete) {
      if (cursorPosition < input.length) {
        const newInput = input.slice(0, cursorPosition) + input.slice(cursorPosition + 1);
        setInput(newInput);
      }
    } else if (key.leftArrow) {
      if (cursorPosition > 0) {
        setCursorPosition(cursorPosition - 1);
      }
    } else if (key.rightArrow) {
      if (cursorPosition < input.length) {
        setCursorPosition(cursorPosition + 1);
      }
    } else if (key.ctrl && inputChar === 'u') {
      setInput('');
      setCursorPosition(0);
    } else if (key.ctrl && inputChar === 'a') {
      setCursorPosition(0);
    } else if (key.ctrl && inputChar === 'e') {
      setCursorPosition(input.length);
    } else if (inputChar && !key.ctrl && !key.meta) {
      // Regular character input
      const newInput = input.slice(0, cursorPosition) + inputChar + input.slice(cursorPosition);
      setInput(newInput);
      setCursorPosition(cursorPosition + 1);
    }
  });

  // Split input into lines for display
  const lines = input.split('\n');
  const isMultiline = lines.length > 1;

  // Calculate which line the cursor is on
  let charsBeforeCursor = 0;
  let cursorLine = 0;
  let cursorCol = cursorPosition;

  for (let i = 0; i < lines.length; i++) {
    if (charsBeforeCursor + lines[i].length >= cursorPosition) {
      cursorLine = i;
      cursorCol = cursorPosition - charsBeforeCursor;
      break;
    }
    charsBeforeCursor += lines[i].length + 1; // +1 for newline
  }

  const renderSingleLine = () => {
    const displayText = input || placeholder;
    const isPlaceholder = !input;

    if (disabled) {
      return (
        <Box>
          <Text color="cyan">{'> '}</Text>
          <Text color="gray">{placeholder}</Text>
        </Box>
      );
    }

    if (isPlaceholder) {
      return (
        <Box>
          <Text color="cyan">{'> '}</Text>
          <Text color="gray">{placeholder}</Text>
        </Box>
      );
    }

    const beforeCursor = input.slice(0, cursorPosition);
    const atCursor = input[cursorPosition] || ' ';
    const afterCursor = input.slice(cursorPosition + 1);

    return (
      <Box>
        <Text color="cyan">{'> '}</Text>
        <Text>{beforeCursor}</Text>
        <Text inverse>{atCursor}</Text>
        <Text>{afterCursor}</Text>
      </Box>
    );
  };

  const renderMultiline = () => {
    return (
      <Box flexDirection="column">
        <Text color="cyan">┌─ multiline ──────────┐</Text>
        {lines.map((line, lineIndex) => {
          const isCurrentLine = lineIndex === cursorLine;
          
          if (isCurrentLine && !disabled) {
            const beforeCursor = line.slice(0, cursorCol);
            const atCursor = line[cursorCol] || ' ';
            const afterCursor = line.slice(cursorCol + 1);
            
            return (
              <Box key={lineIndex}>
                <Text color="cyan">│ </Text>
                <Text>{beforeCursor}</Text>
                <Text inverse>{atCursor}</Text>
                <Text>{afterCursor}</Text>
              </Box>
            );
          } else {
            return (
              <Box key={lineIndex}>
                <Text color="cyan">│ </Text>
                <Text color={disabled ? 'gray' : 'white'}>
                  {line || (lineIndex === 0 && !input ? placeholder : '')}
                </Text>
              </Box>
            );
          }
        })}
        <Text color="cyan">└──────────────────────┘</Text>
      </Box>
    );
  };

  return (
    <Box flexDirection="column" marginY={1}>
      {isMultiline ? renderMultiline() : renderSingleLine()}
      
      {!disabled && (
        <Box marginTop={1}>
          <Text color="gray">
            {isMultiline 
              ? 'Enter: Send • Shift+Enter: New line • Ctrl+U: Clear'
              : 'Enter: Send • Shift+Enter: New line • Ctrl+U: Clear'
            } • {input.length} chars
          </Text>
        </Box>
      )}
    </Box>
  );
};