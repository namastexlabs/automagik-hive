import React, { useState, useCallback, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';

interface ProperMultilineInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const ProperMultilineInput: React.FC<ProperMultilineInputProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'Type your message...',
}) => {
  const [input, setInput] = useState<string>('');
  const [cursorPosition, setCursorPosition] = useState<number>(0);

  // Convert cursor position to row/col
  const lines = input.split('\n');
  let currentRow = 0;
  let currentCol = 0;
  let charCount = 0;

  for (let i = 0; i < lines.length; i++) {
    if (charCount + lines[i].length >= cursorPosition) {
      currentRow = i;
      currentCol = cursorPosition - charCount;
      break;
    }
    charCount += lines[i].length + 1; // +1 for newline
  }

  const isMultiline = lines.length > 1 || input.length > 80;

  const handleSubmit = useCallback(() => {
    if (input.trim() && !disabled) {
      onSubmit(input.trim());
      setInput('');
      setCursorPosition(0);
    }
  }, [input, onSubmit, disabled]);

  const insertText = useCallback((text: string) => {
    const newInput = input.slice(0, cursorPosition) + text + input.slice(cursorPosition);
    setInput(newInput);
    setCursorPosition(cursorPosition + text.length);
  }, [input, cursorPosition]);

  const deleteText = useCallback((direction: 'backward' | 'forward', wordMode = false) => {
    if (direction === 'backward' && cursorPosition > 0) {
      let deleteCount = 1;
      
      if (wordMode) {
        // Meta+Backspace: Delete word
        let pos = cursorPosition - 1;
        
        // Skip whitespace
        while (pos >= 0 && /\s/.test(input[pos])) {
          pos--;
        }
        
        // Delete word characters
        while (pos >= 0 && !/\s/.test(input[pos])) {
          pos--;
        }
        
        deleteCount = cursorPosition - pos - 1;
      }
      
      const newInput = input.slice(0, cursorPosition - deleteCount) + input.slice(cursorPosition);
      setInput(newInput);
      setCursorPosition(cursorPosition - deleteCount);
    } else if (direction === 'forward' && cursorPosition < input.length) {
      let deleteCount = 1;
      
      if (wordMode) {
        // Meta+Delete: Delete word forward
        let pos = cursorPosition;
        
        // Skip whitespace
        while (pos < input.length && /\s/.test(input[pos])) {
          pos++;
        }
        
        // Delete word characters
        while (pos < input.length && !/\s/.test(input[pos])) {
          pos++;
        }
        
        deleteCount = pos - cursorPosition;
      }
      
      const newInput = input.slice(0, cursorPosition) + input.slice(cursorPosition + deleteCount);
      setInput(newInput);
    }
  }, [input, cursorPosition]);

  const moveCursor = useCallback((direction: string, wordMode = false) => {
    switch (direction) {
      case 'left':
        if (wordMode) {
          // Meta+Left: Move by word
          let pos = cursorPosition - 1;
          
          // Skip whitespace
          while (pos >= 0 && /\s/.test(input[pos])) {
            pos--;
          }
          
          // Move to start of word
          while (pos >= 0 && !/\s/.test(input[pos])) {
            pos--;
          }
          
          setCursorPosition(Math.max(0, pos + 1));
        } else {
          setCursorPosition(Math.max(0, cursorPosition - 1));
        }
        break;
        
      case 'right':
        if (wordMode) {
          // Meta+Right: Move by word
          let pos = cursorPosition;
          
          // Skip whitespace
          while (pos < input.length && /\s/.test(input[pos])) {
            pos++;
          }
          
          // Move to end of word
          while (pos < input.length && !/\s/.test(input[pos])) {
            pos++;
          }
          
          setCursorPosition(Math.min(input.length, pos));
        } else {
          setCursorPosition(Math.min(input.length, cursorPosition + 1));
        }
        break;
        
      case 'up':
        if (currentRow > 0) {
          const prevLineLength = lines[currentRow - 1].length;
          const targetCol = Math.min(currentCol, prevLineLength);
          
          // Calculate position in previous line
          let newPos = 0;
          for (let i = 0; i < currentRow - 1; i++) {
            newPos += lines[i].length + 1;
          }
          newPos += targetCol;
          
          setCursorPosition(newPos);
        }
        break;
        
      case 'down':
        if (currentRow < lines.length - 1) {
          const nextLineLength = lines[currentRow + 1].length;
          const targetCol = Math.min(currentCol, nextLineLength);
          
          // Calculate position in next line
          let newPos = 0;
          for (let i = 0; i <= currentRow; i++) {
            newPos += lines[i].length + 1;
          }
          newPos += targetCol;
          
          setCursorPosition(newPos);
        }
        break;
        
      case 'home':
        // Move to start of current line
        const lineStart = cursorPosition - currentCol;
        setCursorPosition(lineStart);
        break;
        
      case 'end':
        // Move to end of current line
        const lineEnd = cursorPosition - currentCol + lines[currentRow].length;
        setCursorPosition(lineEnd);
        break;
    }
  }, [input, cursorPosition, currentRow, currentCol, lines]);

  useInput((inputChar, key) => {
    if (disabled) return;

    // Submit handling
    if (key.return) {
      if (key.ctrl || (!isMultiline && !key.shift)) {
        // Ctrl+Enter or Enter in single-line mode = submit
        handleSubmit();
      } else {
        // Shift+Enter or Enter in multiline mode = new line
        insertText('\n');
      }
      return;
    }

    // Navigation with word movement support
    if (key.leftArrow) {
      moveCursor('left', key.meta);
      return;
    }
    if (key.rightArrow) {
      moveCursor('right', key.meta);
      return;
    }
    if (key.upArrow) {
      moveCursor('up');
      return;
    }
    if (key.downArrow) {
      moveCursor('down');
      return;
    }

    // Home/End keys with Ctrl
    if (key.ctrl && key.leftArrow) {
      moveCursor('home');
      return;
    }
    if (key.ctrl && key.rightArrow) {
      moveCursor('end');
      return;
    }

    // Deletion with word support
    if (key.backspace) {
      deleteText('backward', key.meta);
      return;
    }
    if (key.delete) {
      deleteText('forward', key.meta);
      return;
    }

    // Clear shortcuts
    if (key.ctrl && inputChar === 'u') {
      setInput('');
      setCursorPosition(0);
      return;
    }
    if (key.ctrl && inputChar === 'k') {
      // Delete to end of line
      const lineEnd = cursorPosition - currentCol + lines[currentRow].length;
      const newInput = input.slice(0, cursorPosition) + input.slice(lineEnd);
      setInput(newInput);
      return;
    }

    // Select all
    if (key.ctrl && inputChar === 'a') {
      setCursorPosition(0);
      // Note: We don't have selection support in this simple implementation
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
      const maxLines = 6;
      const visibleLines = lines.slice(0, maxLines);
      
      return (
        <Box flexDirection="column">
          <Text color="cyan">┌─ <Text color="yellow">multiline</Text> ─ {lines.length} lines, {input.length} chars ─┐</Text>
          {visibleLines.map((line, lineIndex) => {
            const isCurrentLine = lineIndex === currentRow;
            
            if (isCurrentLine && !disabled) {
              const beforeCursor = line.slice(0, currentCol);
              const atCursor = line[currentCol] || ' ';
              const afterCursor = line.slice(currentCol + 1);
              
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
          {lines.length > maxLines && (
            <Box>
              <Text color="cyan">│ </Text>
              <Text color="gray">... {lines.length - maxLines} more lines</Text>
            </Box>
          )}
          <Text color="cyan">└{'─'.repeat(50)}┘</Text>
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
          <Text inverse>{atCursor}</Text>
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
              ? 'Ctrl+Enter: Send • Enter: New line • Cmd+←/→: Word jump • Cmd+Backspace: Delete word'
              : 'Enter: Send • Shift+Enter: New line • Cmd+←/→: Word jump'
            }
          </Text>
        </Box>
      )}
    </Box>
  );
};