import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Box, Text, useInput, useStdin } from 'ink';

interface MultilineInputPromptProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxHeight?: number;
  inputWidth?: number;
}

export const MultilineInputPrompt: React.FC<MultilineInputPromptProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'Type your message...',
  maxHeight = 10,
  inputWidth = 80,
}) => {
  const { isRawModeSupported } = useStdin();
  
  // Input state
  const [lines, setLines] = useState<string[]>(['']);
  const [cursorRow, setCursorRow] = useState<number>(0);
  const [cursorCol, setCursorCol] = useState<number>(0);
  const [isMultiline, setIsMultiline] = useState<boolean>(false);
  
  // Calculate visible area
  const visibleLines = Math.min(lines.length, maxHeight);
  const scrollOffset = Math.max(0, cursorRow - maxHeight + 1);
  const visibleLinesSlice = lines.slice(scrollOffset, scrollOffset + visibleLines);
  
  const currentLine = lines[cursorRow] || '';
  const inputText = lines.join('\n');
  
  const wrapText = useCallback((text: string, width: number): string[] => {
    if (!text) return [''];
    
    const lines: string[] = [];
    const rawLines = text.split('\n');
    
    for (const line of rawLines) {
      if (line.length <= width) {
        lines.push(line);
      } else {
        // Wrap long lines
        for (let i = 0; i < line.length; i += width) {
          lines.push(line.slice(i, i + width));
        }
      }
    }
    
    return lines.length > 0 ? lines : [''];
  }, []);
  
  const insertAtCursor = useCallback((text: string) => {
    const newLines = [...lines];
    const before = currentLine.slice(0, cursorCol);
    const after = currentLine.slice(cursorCol);
    
    if (text.includes('\n') || text.length > 100) {
      // Handle multiline paste or large content
      const pastedLines = text.split('\n');
      
      // If it's a single long line, wrap it
      if (pastedLines.length === 1 && text.length > inputWidth - 10) {
        const wrappedLines = wrapText(text, inputWidth - 10);
        newLines[cursorRow] = before + wrappedLines[0];
        
        for (let i = 1; i < wrappedLines.length; i++) {
          newLines.splice(cursorRow + i, 0, wrappedLines[i]);
        }
        
        newLines[cursorRow + wrappedLines.length - 1] += after;
        setLines(newLines);
        setCursorRow(cursorRow + wrappedLines.length - 1);
        setCursorCol(newLines[cursorRow + wrappedLines.length - 1].length - after.length);
      } else {
        // Handle true multiline content
        newLines[cursorRow] = before + pastedLines[0];
        
        // Insert additional lines
        for (let i = 1; i < pastedLines.length; i++) {
          newLines.splice(cursorRow + i, 0, pastedLines[i]);
        }
        
        // Update the last pasted line with the after text
        const lastPastedIndex = cursorRow + pastedLines.length - 1;
        newLines[lastPastedIndex] = newLines[lastPastedIndex] + after;
        
        setLines(newLines);
        setCursorRow(lastPastedIndex);
        setCursorCol(newLines[lastPastedIndex].length - after.length);
      }
      
      // Auto-enable multiline mode for large pastes
      setIsMultiline(true);
    } else {
      // Single line insertion
      const newContent = before + text + after;
      
      // Auto-wrap if line becomes too long
      if (newContent.length > inputWidth - 10) {
        const wrappedLines = wrapText(newContent, inputWidth - 10);
        newLines[cursorRow] = wrappedLines[0];
        
        for (let i = 1; i < wrappedLines.length; i++) {
          newLines.splice(cursorRow + i, 0, wrappedLines[i]);
        }
        
        setLines(newLines);
        if (wrappedLines.length > 1) {
          setIsMultiline(true);
        }
        setCursorCol(cursorCol + text.length);
      } else {
        newLines[cursorRow] = newContent;
        setLines(newLines);
        setCursorCol(cursorCol + text.length);
      }
    }
  }, [lines, cursorRow, cursorCol, currentLine, inputWidth, wrapText]);
  
  const deleteAtCursor = useCallback((direction: 'backward' | 'forward' = 'backward') => {
    const newLines = [...lines];
    
    if (direction === 'backward') {
      if (cursorCol > 0) {
        // Delete character before cursor
        const newLine = currentLine.slice(0, cursorCol - 1) + currentLine.slice(cursorCol);
        newLines[cursorRow] = newLine;
        setLines(newLines);
        setCursorCol(cursorCol - 1);
      } else if (cursorRow > 0) {
        // Merge with previous line
        const prevLine = lines[cursorRow - 1];
        const mergedLine = prevLine + currentLine;
        newLines[cursorRow - 1] = mergedLine;
        newLines.splice(cursorRow, 1);
        setLines(newLines);
        setCursorRow(cursorRow - 1);
        setCursorCol(prevLine.length);
      }
    } else {
      if (cursorCol < currentLine.length) {
        // Delete character after cursor
        const newLine = currentLine.slice(0, cursorCol) + currentLine.slice(cursorCol + 1);
        newLines[cursorRow] = newLine;
        setLines(newLines);
      } else if (cursorRow < lines.length - 1) {
        // Merge with next line
        const nextLine = lines[cursorRow + 1];
        const mergedLine = currentLine + nextLine;
        newLines[cursorRow] = mergedLine;
        newLines.splice(cursorRow + 1, 1);
        setLines(newLines);
      }
    }
  }, [lines, cursorRow, cursorCol, currentLine]);
  
  const handleSubmit = useCallback(() => {
    const text = inputText.trim();
    if (text && !disabled) {
      onSubmit(text);
      setLines(['']);
      setCursorRow(0);
      setCursorCol(0);
      setIsMultiline(false);
    }
  }, [inputText, onSubmit, disabled]);
  
  const moveCursor = useCallback((direction: 'up' | 'down' | 'left' | 'right' | 'home' | 'end') => {
    switch (direction) {
      case 'left':
        if (cursorCol > 0) {
          setCursorCol(cursorCol - 1);
        } else if (cursorRow > 0) {
          setCursorRow(cursorRow - 1);
          setCursorCol(lines[cursorRow - 1]?.length || 0);
        }
        break;
      case 'right':
        if (cursorCol < currentLine.length) {
          setCursorCol(cursorCol + 1);
        } else if (cursorRow < lines.length - 1) {
          setCursorRow(cursorRow + 1);
          setCursorCol(0);
        }
        break;
      case 'up':
        if (cursorRow > 0) {
          setCursorRow(cursorRow - 1);
          setCursorCol(Math.min(cursorCol, lines[cursorRow - 1]?.length || 0));
        }
        break;
      case 'down':
        if (cursorRow < lines.length - 1) {
          setCursorRow(cursorRow + 1);
          setCursorCol(Math.min(cursorCol, lines[cursorRow + 1]?.length || 0));
        }
        break;
      case 'home':
        setCursorCol(0);
        break;
      case 'end':
        setCursorCol(currentLine.length);
        break;
    }
  }, [cursorRow, cursorCol, currentLine, lines]);
  
  const addNewLine = useCallback(() => {
    const newLines = [...lines];
    const before = currentLine.slice(0, cursorCol);
    const after = currentLine.slice(cursorCol);
    
    newLines[cursorRow] = before;
    newLines.splice(cursorRow + 1, 0, after);
    
    setLines(newLines);
    setCursorRow(cursorRow + 1);
    setCursorCol(0);
    setIsMultiline(true);
  }, [lines, cursorRow, cursorCol, currentLine]);
  
  useInput((inputChar: string, key: any) => {
    if (disabled) return;
    
    // Submit handling
    if (key.return) {
      if (key.ctrl || (!isMultiline && !key.shift)) {
        // Ctrl+Enter or Enter in single-line mode = submit
        handleSubmit();
      } else {
        // Shift+Enter or Enter in multiline mode = new line
        addNewLine();
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
    if (key.upArrow) {
      moveCursor('up');
      return;
    }
    if (key.downArrow) {
      moveCursor('down');
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
      deleteAtCursor('backward');
      return;
    }
    if (key.delete) {
      deleteAtCursor('forward');
      return;
    }
    
    // Clear input
    if (key.ctrl && inputChar === 'u') {
      setLines(['']);
      setCursorRow(0);
      setCursorCol(0);
      setIsMultiline(false);
      return;
    }
    
    // Toggle multiline mode
    if (key.ctrl && inputChar === 'm') {
      setIsMultiline(!isMultiline);
      return;
    }
    
    // Regular character input
    if (inputChar && !key.ctrl && !key.meta && inputChar.length === 1) {
      const charCode = inputChar.charCodeAt(0);
      if (charCode >= 32 || charCode === 9) { // Printable chars and tab
        insertAtCursor(inputChar);
      }
    }
  });
  
  // Handle paste events
  useEffect(() => {
    if (!isRawModeSupported) return;
    
    const handlePaste = (data: string) => {
      const cleanData = data
        .replace(/[\x00-\x08\x0E-\x1F\x7F]/g, '') // Remove control chars
        .replace(/\r\n/g, '\n') // Normalize line endings
        .replace(/\r/g, '\n');
      
      if (cleanData.length > 0) {
        insertAtCursor(cleanData);
      }
    };
    
    // This is a simplified paste handler - real clipboard detection is limited in Ink
    return () => {};
  }, [insertAtCursor, isRawModeSupported]);
  
  const renderInput = () => {
    const effectiveWidth = inputWidth - 4; // Account for prompt and borders
    
    if (isMultiline || lines.length > 1) {
      return (
        <Box flexDirection="column">
          <Text color="cyan">{'┌─ '}<Text color="yellow">multiline</Text>{' ─'.repeat(Math.max(0, (effectiveWidth - 12) / 2))}{'─┐'}</Text>
          {visibleLinesSlice.map((line, index) => {
            const actualRow = scrollOffset + index;
            const isCurrentRow = actualRow === cursorRow;
            const displayLine = line || (isCurrentRow ? ' ' : '');
            
            if (isCurrentRow && !disabled) {
              const beforeCursor = displayLine.slice(0, cursorCol);
              const atCursor = displayLine[cursorCol] || ' ';
              const afterCursor = displayLine.slice(cursorCol + 1);
              
              return (
                <Box key={actualRow}>
                  <Text color="cyan">{'│ '}</Text>
                  <Text>{beforeCursor}</Text>
                  <Text inverse={true}>{atCursor}</Text>
                  <Text>{afterCursor}</Text>
                </Box>
              );
            } else {
              return (
                <Box key={actualRow}>
                  <Text color="cyan">{'│ '}</Text>
                  <Text color={disabled ? 'gray' : 'white'}>
                    {displayLine || (actualRow === 0 && !inputText ? placeholder : '')}
                  </Text>
                </Box>
              );
            }
          })}
          <Text color="cyan">{'└'}{('─'.repeat(effectiveWidth))}{'┘'}</Text>
          {lines.length > maxHeight && (
            <Text color="gray" dimColor>
              {scrollOffset > 0 ? '↑ ' : '  '}
              Line {cursorRow + 1}/{lines.length}
              {scrollOffset + visibleLines < lines.length ? ' ↓' : ''}
            </Text>
          )}
        </Box>
      );
    } else {
      // Single line mode
      const displayText = inputText || placeholder;
      const isPlaceholder = !inputText;
      
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
      
      const beforeCursor = inputText.slice(0, cursorCol);
      const atCursor = inputText[cursorCol] || ' ';
      const afterCursor = inputText.slice(cursorCol + 1);
      
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
    const mode = isMultiline || lines.length > 1 ? 'multi' : 'single';
    const charCount = inputText.length;
    const lineCount = lines.length;
    
    let status = `${mode} • ${charCount} chars`;
    if (isMultiline || lines.length > 1) {
      status += ` • ${lineCount} lines`;
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
          <Text color="gray" dimColor>
            {isMultiline || lines.length > 1 
              ? 'Ctrl+Enter: Send • Enter: New line • Ctrl+M: Toggle mode'
              : 'Enter: Send • Shift+Enter: New line • Ctrl+M: Multiline mode'
            }
          </Text>
        </Box>
      )}
    </Box>
  );
};