import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Box, Text, useInput, useStdin } from 'ink';

interface EnhancedInputPromptProps {
  onSubmit: (message: string) => void;
  inputWidth: number;
  disabled?: boolean;
  placeholder?: string;
  multiline?: boolean;
  maxLines?: number;
}

interface InputHistory {
  messages: string[];
  currentIndex: number;
}

export const EnhancedInputPrompt: React.FC<EnhancedInputPromptProps> = ({
  onSubmit,
  inputWidth,
  disabled = false,
  placeholder = 'Type your message...',
  multiline = true,
  maxLines = 10,
}) => {
  const { isRawModeSupported } = useStdin();
  
  // Input state
  const [input, setInput] = useState<string>('');
  const [lines, setLines] = useState<string[]>(['']);
  const [cursorLine, setCursorLine] = useState<number>(0);
  const [cursorCol, setCursorCol] = useState<number>(0);
  
  // History state
  const [history, setHistory] = useState<InputHistory>({ messages: [], currentIndex: -1 });
  const [isInHistory, setIsInHistory] = useState<boolean>(false);
  const tempInput = useRef<string>('');
  
  // Selection state
  const [isMultilineMode, setIsMultilineMode] = useState<boolean>(false);
  const [showHelp, setShowHelp] = useState<boolean>(false);

  // Convert between single string and lines array
  useEffect(() => {
    if (isMultilineMode) {
      const newLines = input.split('\n');
      if (newLines.join('\n') !== lines.join('\n')) {
        setLines(newLines);
        // Adjust cursor position if needed
        if (cursorLine >= newLines.length) {
          setCursorLine(Math.max(0, newLines.length - 1));
        }
        if (newLines[cursorLine] && cursorCol > newLines[cursorLine].length) {
          setCursorCol(newLines[cursorLine].length);
        }
      }
    } else {
      const singleLine = input.replace(/\n/g, ' ');
      if (singleLine !== input) {
        setInput(singleLine);
      }
      setLines([singleLine]);
      setCursorLine(0);
    }
  }, [input, isMultilineMode, cursorLine, cursorCol, lines]);

  const updateInputFromLines = useCallback(() => {
    const newInput = lines.join('\n');
    if (newInput !== input) {
      setInput(newInput);
    }
  }, [lines, input]);

  const getCurrentLine = useCallback(() => lines[cursorLine] || '', [lines, cursorLine]);
  
  const insertAtCursor = useCallback((text: string) => {
    const currentLine = getCurrentLine();
    const newLine = currentLine.slice(0, cursorCol) + text + currentLine.slice(cursorCol);
    const newLines = [...lines];
    newLines[cursorLine] = newLine;
    setLines(newLines);
    setCursorCol(cursorCol + text.length);
    
    // Update input state
    const newInput = newLines.join('\n');
    setInput(newInput);
    
    // Clear history navigation if active
    if (isInHistory) {
      setIsInHistory(false);
      setHistory(prev => ({ ...prev, currentIndex: -1 }));
    }
  }, [lines, cursorLine, cursorCol, getCurrentLine, isInHistory, setHistory]);

  const deleteAtCursor = useCallback((direction: 'backward' | 'forward' = 'backward') => {
    const currentLine = getCurrentLine();
    
    if (direction === 'backward') {
      if (cursorCol > 0) {
        // Delete character before cursor
        const newLine = currentLine.slice(0, cursorCol - 1) + currentLine.slice(cursorCol);
        const newLines = [...lines];
        newLines[cursorLine] = newLine;
        setLines(newLines);
        setCursorCol(cursorCol - 1);
        
        // Update input state
        const newInput = newLines.join('\n');
        setInput(newInput);
        
        // Clear history navigation if active
        if (isInHistory) {
          setIsInHistory(false);
          setHistory(prev => ({ ...prev, currentIndex: -1 }));
        }
      } else if (cursorLine > 0 && isMultilineMode) {
        // Merge with previous line
        const prevLine = lines[cursorLine - 1];
        const newLine = prevLine + currentLine;
        const newLines = lines.filter((_, i) => i !== cursorLine);
        newLines[cursorLine - 1] = newLine;
        setLines(newLines);
        setCursorLine(cursorLine - 1);
        setCursorCol(prevLine.length);
        
        // Update input state
        const newInput = newLines.join('\n');
        setInput(newInput);
      }
    } else {
      if (cursorCol < currentLine.length) {
        // Delete character after cursor
        const newLine = currentLine.slice(0, cursorCol) + currentLine.slice(cursorCol + 1);
        const newLines = [...lines];
        newLines[cursorLine] = newLine;
        setLines(newLines);
        
        // Update input state
        const newInput = newLines.join('\n');
        setInput(newInput);
        
        // Clear history navigation if active
        if (isInHistory) {
          setIsInHistory(false);
          setHistory(prev => ({ ...prev, currentIndex: -1 }));
        }
      } else if (cursorLine < lines.length - 1 && isMultilineMode) {
        // Merge with next line
        const nextLine = lines[cursorLine + 1];
        const newLine = currentLine + nextLine;
        const newLines = [...lines];
        newLines[cursorLine] = newLine;
        newLines.splice(cursorLine + 1, 1);
        setLines(newLines);
        
        // Update input state
        const newInput = newLines.join('\n');
        setInput(newInput);
      }
    }
  }, [lines, cursorLine, cursorCol, getCurrentLine, isMultilineMode, isInHistory, setHistory]);

  const handleSubmit = useCallback(() => {
    if (input.trim() && !disabled) {
      // Add to history
      setHistory(prev => ({
        messages: [...prev.messages, input].slice(-50), // Keep last 50 messages
        currentIndex: -1,
      }));
      
      onSubmit(input.trim());
      setInput('');
      setLines(['']);
      setCursorLine(0);
      setCursorCol(0);
      setIsInHistory(false);
      tempInput.current = '';
    }
  }, [input, onSubmit, disabled]);

  const navigateHistory = useCallback((direction: 'up' | 'down') => {
    if (history.messages.length === 0) return;

    if (!isInHistory && direction === 'up') {
      // First time entering history - save current input
      tempInput.current = input;
      setIsInHistory(true);
      const newIndex = history.messages.length - 1;
      setHistory(prev => ({ ...prev, currentIndex: newIndex }));
      const historicalMessage = history.messages[newIndex];
      setInput(historicalMessage);
      setLines(historicalMessage.split('\n'));
      setCursorLine(0);
      setCursorCol(0);
    } else if (isInHistory) {
      if (direction === 'up' && history.currentIndex > 0) {
        const newIndex = history.currentIndex - 1;
        setHistory(prev => ({ ...prev, currentIndex: newIndex }));
        const historicalMessage = history.messages[newIndex];
        setInput(historicalMessage);
        setLines(historicalMessage.split('\n'));
        setCursorLine(0);
        setCursorCol(0);
      } else if (direction === 'down') {
        if (history.currentIndex < history.messages.length - 1) {
          const newIndex = history.currentIndex + 1;
          setHistory(prev => ({ ...prev, currentIndex: newIndex }));
          const historicalMessage = history.messages[newIndex];
          setInput(historicalMessage);
          setLines(historicalMessage.split('\n'));
          setCursorLine(0);
          setCursorCol(0);
        } else {
          // Return to current input
          setIsInHistory(false);
          setHistory(prev => ({ ...prev, currentIndex: -1 }));
          setInput(tempInput.current);
          setLines(tempInput.current.split('\n'));
          setCursorLine(0);
          setCursorCol(0);
        }
      }
    }
  }, [history, input, isInHistory]);

  useInput((inputChar: string, key: any) => {
    if (disabled) {
      return;
    }

    // Help toggle
    if (key.ctrl && inputChar === 'h') {
      setShowHelp(!showHelp);
      return;
    }

    // Submit handling
    if (key.return) {
      if (isMultilineMode && !key.ctrl) {
        // Add new line in multiline mode
        if (lines.length < maxLines) {
          const currentLine = getCurrentLine();
          const beforeCursor = currentLine.slice(0, cursorCol);
          const afterCursor = currentLine.slice(cursorCol);
          
          const newLines = [...lines];
          newLines[cursorLine] = beforeCursor;
          newLines.splice(cursorLine + 1, 0, afterCursor);
          
          setLines(newLines);
          setCursorLine(cursorLine + 1);
          setCursorCol(0);
          setInput(newLines.join('\n'));
        }
      } else {
        // Submit (Enter in single-line mode, or Ctrl+Enter in multiline mode)
        handleSubmit();
      }
      return;
    }

    // History navigation
    if (key.upArrow) {
      navigateHistory('up');
      return;
    }
    if (key.downArrow) {
      navigateHistory('down');
      return;
    }

    // Clear any history navigation
    if (isInHistory && inputChar && !key.upArrow && !key.downArrow && !key.ctrl) {
      setIsInHistory(false);
      setHistory(prev => ({ ...prev, currentIndex: -1 }));
    }

    // Cursor movement
    if (key.leftArrow) {
      if (cursorCol > 0) {
        setCursorCol(cursorCol - 1);
      } else if (cursorLine > 0 && isMultilineMode) {
        setCursorLine(cursorLine - 1);
        setCursorCol(lines[cursorLine - 1]?.length || 0);
      }
      return;
    }
    if (key.rightArrow) {
      const currentLine = getCurrentLine();
      if (cursorCol < currentLine.length) {
        setCursorCol(cursorCol + 1);
      } else if (cursorLine < lines.length - 1 && isMultilineMode) {
        setCursorLine(cursorLine + 1);
        setCursorCol(0);
      }
      return;
    }

    // Deletion
    if (key.backspace) {
      deleteAtCursor('backward');
      return;
    }
    if (key.delete) {
      deleteAtCursor('forward');
      return;
    }

    // Text editing shortcuts
    if (key.ctrl && inputChar === 'a') {
      setCursorCol(0);
      return;
    }
    if (key.ctrl && inputChar === 'e') {
      setCursorCol(getCurrentLine().length);
      return;
    }
    if (key.ctrl && inputChar === 'u') {
      setInput('');
      setLines(['']);
      setCursorLine(0);
      setCursorCol(0);
      return;
    }
    if (key.ctrl && inputChar === 'k') {
      const currentLine = getCurrentLine();
      const newLine = currentLine.slice(0, cursorCol);
      const newLines = [...lines];
      newLines[cursorLine] = newLine;
      setLines(newLines);
      setInput(newLines.join('\n'));
      return;
    }

    // Word navigation (fix the word boundary detection)
    if (key.ctrl && key.leftArrow) {
      const currentLine = getCurrentLine();
      let newCol = cursorCol;
      
      // Skip spaces backwards
      while (newCol > 0 && currentLine[newCol - 1] === ' ') {
        newCol--;
      }
      
      // Find word boundary
      while (newCol > 0 && currentLine[newCol - 1] !== ' ') {
        newCol--;
      }
      
      setCursorCol(newCol);
      return;
    }
    if (key.ctrl && key.rightArrow) {
      const currentLine = getCurrentLine();
      let newCol = cursorCol;
      
      // Skip spaces forward
      while (newCol < currentLine.length && currentLine[newCol] === ' ') {
        newCol++;
      }
      
      // Find word boundary
      while (newCol < currentLine.length && currentLine[newCol] !== ' ') {
        newCol++;
      }
      
      setCursorCol(newCol);
      return;
    }

    // Mode toggle
    if (key.ctrl && inputChar === 'm') {
      setIsMultilineMode(!isMultilineMode);
      return;
    }

    // Clipboard paste handling (Ctrl+V)
    if (key.ctrl && inputChar === 'v') {
      // In a real terminal environment, this would handle clipboard
      // For now, we'll just prevent the default behavior
      return;
    }

    // Regular character input - improved filtering
    if (inputChar && !key.ctrl && !key.meta && !key.alt && inputChar.length === 1) {
      // Filter out control characters except newlines
      const charCode = inputChar.charCodeAt(0);
      if (charCode >= 32 || charCode === 9) { // Allow printable chars and tab
        insertAtCursor(inputChar);
      }
    }
  });

  // Handle paste events with better character filtering
  useEffect(() => {
    if (isRawModeSupported) {
      const handlePaste = (data: string) => {
        // Filter out control characters and normalize the text
        const filteredData = data
          .replace(/[\x00-\x08\x0E-\x1F\x7F]/g, '') // Remove control chars except \t, \n, \r
          .replace(/\r\n/g, '\n') // Normalize line endings
          .replace(/\r/g, '\n'); // Convert remaining \r to \n
        
        if (filteredData.length > 0) {
          insertAtCursor(filteredData);
        }
      };

      // This is a basic implementation - real paste detection is limited in Ink
      return () => {}; // Cleanup if needed
    }
    return undefined; // Explicit return for all code paths
  }, [insertAtCursor, isRawModeSupported]);

  const renderInput = () => {
    const effectiveWidth = Math.min(inputWidth - 4, 120);
    
    if (isMultilineMode) {
      return (
        <Box flexDirection="column">
          <Text color="cyan">{'┌─ '}<Text color="yellow">multiline mode</Text>{' ─'.repeat(Math.max(0, (effectiveWidth - 20) / 2))}{'─┐'}</Text>
          {lines.map((line, lineIndex) => {
            const isCurrentLine = lineIndex === cursorLine;
            const displayLine = line || (isCurrentLine ? ' ' : '');
            
            if (isCurrentLine && !disabled) {
              const beforeCursor = displayLine.slice(0, cursorCol);
              const atCursor = displayLine[cursorCol] || ' ';
              const afterCursor = displayLine.slice(cursorCol + 1);
              
              return (
                <Box key={lineIndex}>
                  <Text color="cyan">{'│ '}</Text>
                  <Text>{beforeCursor}</Text>
                  <Text inverse={true}>{atCursor}</Text>
                  <Text>{afterCursor}</Text>
                </Box>
              );
            } else {
              return (
                <Box key={lineIndex}>
                  <Text color="cyan">{'│ '}</Text>
                  <Text color={disabled ? 'gray' : 'white'}>
                    {displayLine || (lineIndex === 0 && !input ? placeholder : '')}
                  </Text>
                </Box>
              );
            }
          })}
          <Text color="cyan">{'└'}{('─'.repeat(effectiveWidth))}{'┘'}</Text>
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
      
      const beforeCursor = input.slice(0, cursorCol);
      const atCursor = input[cursorCol] || ' ';
      const afterCursor = input.slice(cursorCol + 1);
      
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

  const getStatusText = () => {
    const mode = isMultilineMode ? 'multi' : 'single';
    const charCount = input.length;
    const lineCount = lines.length;
    
    let status = `${mode} • ${charCount} chars`;
    if (isMultilineMode) {
      status += ` • ${lineCount} lines`;
    }
    if (isInHistory) {
      status += ` • history ${history.currentIndex + 1}/${history.messages.length}`;
    }
    
    return status;
  };

  return (
    <Box flexDirection="column" marginY={1}>
      {renderInput()}
      
      {!disabled && (
        <Box flexDirection="column" marginTop={1}>
          <Text color="gray" dimColor>
            {getStatusText()}
          </Text>
          
          {showHelp && (
            <Box flexDirection="column" marginTop={1} padding={1} borderStyle="round" borderColor="blue">
              <Text bold color="blue">Enhanced Input Controls:</Text>
              <Text>• <Text color="cyan">Enter</Text>: Send message (single-line) / New line (multi-line)</Text>
              <Text>• <Text color="cyan">Ctrl+Enter</Text>: Send message (multi-line mode)</Text>
              <Text>• <Text color="cyan">Ctrl+M</Text>: Toggle single/multi-line mode</Text>
              <Text>• <Text color="cyan">↑/↓</Text>: Navigate message history</Text>
              <Text>• <Text color="cyan">Ctrl+A/E</Text>: Move to start/end of line</Text>
              <Text>• <Text color="cyan">Ctrl+U</Text>: Clear input</Text>
              <Text>• <Text color="cyan">Ctrl+K</Text>: Delete to end of line</Text>
              <Text>• <Text color="cyan">Ctrl+←/→</Text>: Move by word</Text>
              <Text>• <Text color="cyan">Ctrl+H</Text>: Toggle this help</Text>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};