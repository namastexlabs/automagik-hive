import React, { useState, useCallback } from 'react';
import { Box, Text, useInput } from 'ink';

interface WorkingInputPromptProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  inputWidth?: number;
}

export const WorkingInputPrompt: React.FC<WorkingInputPromptProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'Type your message...',
  inputWidth = 80,
}) => {
  const [input, setInput] = useState<string>('');
  const [cursorPosition, setCursorPosition] = useState<number>(0);
  const [lines, setLines] = useState<string[]>(['']);
  const [currentLine, setCurrentLine] = useState<number>(0);
  const [currentCol, setCurrentCol] = useState<number>(0);

  const isMultiline = lines.length > 1 || lines[0].includes('\n');
  const displayLines = input.split('\n');
  const maxDisplayLines = Math.min(displayLines.length, 6);

  const handleSubmit = useCallback(() => {
    if (input.trim() && !disabled) {
      onSubmit(input.trim());
      setInput('');
      setCursorPosition(0);
      setLines(['']);
      setCurrentLine(0);
      setCurrentCol(0);
    }
  }, [input, onSubmit, disabled]);

  const insertText = useCallback((text: string) => {
    const newInput = input.slice(0, cursorPosition) + text + input.slice(cursorPosition);
    setInput(newInput);
    setCursorPosition(cursorPosition + text.length);
    
    // Update lines array
    const newLines = newInput.split('\n');
    setLines(newLines);
  }, [input, cursorPosition]);

  const deleteChar = useCallback((direction: 'backward' | 'forward' = 'backward') => {
    if (direction === 'backward' && cursorPosition > 0) {
      const newInput = input.slice(0, cursorPosition - 1) + input.slice(cursorPosition);
      setInput(newInput);
      setCursorPosition(cursorPosition - 1);
      
      // Update lines array
      const newLines = newInput.split('\n');
      setLines(newLines);
    } else if (direction === 'forward' && cursorPosition < input.length) {
      const newInput = input.slice(0, cursorPosition) + input.slice(cursorPosition + 1);
      setInput(newInput);
      
      // Update lines array
      const newLines = newInput.split('\n');
      setLines(newLines);
    }
  }, [input, cursorPosition]);

  const moveCursor = useCallback((direction: 'left' | 'right' | 'home' | 'end') => {
    switch (direction) {
      case 'left':
        if (cursorPosition > 0) {
          setCursorPosition(cursorPosition - 1);
        }
        break;
      case 'right':
        if (cursorPosition < input.length) {
          setCursorPosition(cursorPosition + 1);
        }
        break;
      case 'home':
        // Find start of current line
        const lineStart = input.lastIndexOf('\n', cursorPosition - 1) + 1;
        setCursorPosition(lineStart);
        break;
      case 'end':
        // Find end of current line
        const lineEnd = input.indexOf('\n', cursorPosition);
        setCursorPosition(lineEnd === -1 ? input.length : lineEnd);
        break;
    }
  }, [cursorPosition, input]);

  useInput((inputChar: string, key: any) => {
    if (disabled) return;

    // Submit handling
    if (key.return) {
      if (key.ctrl) {
        // Ctrl+Enter always submits
        handleSubmit();
      } else if (key.shift || isMultiline) {
        // Shift+Enter or multiline mode adds new line
        insertText('\n');
      } else {
        // Regular Enter submits in single line mode
        handleSubmit();
      }
      return;
    }

    // Navigation
    if (key.leftArrow) {
      moveCursor('left');
      return;
    }
    if (key.rightArrow) {
      moveCursor('right');
      return;
    }

    // Home/End
    if (key.ctrl && key.leftArrow) {
      moveCursor('home');
      return;
    }
    if (key.ctrl && key.rightArrow) {
      moveCursor('end');
      return;
    }

    // Deletion
    if (key.backspace) {
      deleteChar('backward');
      return;
    }
    if (key.delete) {
      deleteChar('forward');
      return;
    }

    // Clear input
    if (key.ctrl && inputChar === 'u') {
      setInput('');
      setCursorPosition(0);
      setLines(['']);
      setCurrentLine(0);
      setCurrentCol(0);
      return;
    }

    // Regular character input
    if (inputChar && !key.ctrl && !key.meta && inputChar.length === 1) {
      const charCode = inputChar.charCodeAt(0);
      if (charCode >= 32 || charCode === 9) { // Printable chars and tab
        insertText(inputChar);
      }
    }
  });

  const renderInput = () => {
    if (isMultiline) {
      return (
        <Box flexDirection="column">
          <Text color="cyan">{'┌─ '}<Text color="yellow">multiline</Text>{' ─'.repeat(Math.max(0, (inputWidth - 20) / 2))}{'─┐'}</Text>
          {displayLines.slice(0, maxDisplayLines).map((line, index) => {
            // Calculate cursor position for this line
            const lineStart = displayLines.slice(0, index).join('\n').length + (index > 0 ? 1 : 0);
            const lineEnd = lineStart + line.length;
            const showCursor = cursorPosition >= lineStart && cursorPosition <= lineEnd;
            
            let beforeCursor = line;
            let atCursor = ' ';
            let afterCursor = '';
            
            if (showCursor && !disabled) {
              const relativePos = cursorPosition - lineStart;
              beforeCursor = line.slice(0, relativePos);
              atCursor = line[relativePos] || ' ';
              afterCursor = line.slice(relativePos + 1);
            }
            
            return (
              <Box key={index}>
                <Text color="cyan">{'│ '}</Text>
                {showCursor && !disabled ? (
                  <>
                    <Text>{beforeCursor}</Text>
                    <Text inverse={true}>{atCursor}</Text>
                    <Text>{afterCursor}</Text>
                  </>
                ) : (
                  <Text color={disabled ? 'gray' : 'white'}>
                    {line || (index === 0 && !input ? placeholder : '')}
                  </Text>
                )}
              </Box>
            );
          })}
          <Text color="cyan">{'└'}{('─'.repeat(inputWidth - 4))}{'┘'}</Text>
          {displayLines.length > maxDisplayLines && (
            <Text color="gray" dimColor>
              ... {displayLines.length - maxDisplayLines} more lines
            </Text>
          )}
        </Box>
      );
    } else {
      // Single line mode
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
          <Text inverse={true}>{atCursor}</Text>
          <Text>{afterCursor}</Text>
        </Box>
      );
    }
  };

  return (
    <Box flexDirection="column" marginY={1}>
      {renderInput()}
      
      {!disabled && (
        <Box marginTop={1}>
          <Text color="gray">
            {isMultiline 
              ? 'Ctrl+Enter: Send • Enter: New line • Shift+Enter: New line'
              : 'Enter: Send • Shift+Enter: New line • Ctrl+Enter: Send'
            } • {input.length} chars
          </Text>
        </Box>
      )}
    </Box>
  );
};