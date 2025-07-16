/**
 * Simplified InputPrompt component inspired by gemini-cli
 * Focuses on the core text editing functionality
 */

import React, { useCallback, useState, useRef } from 'react';
import { Box, Text } from 'ink';
import { useKeypress, Key } from '../hooks/useKeypress.js';
import { cpSlice, cpLen, toCodePoints } from '../utils/textUtils.js';
import stringWidth from 'string-width';
import stripAnsi from 'strip-ansi';

interface GeminiInputPromptProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  focus?: boolean;
  inputWidth?: number;
}

// Simple helper for word-wise ops
function isWordChar(ch: string | undefined): boolean {
  if (ch === undefined) {
    return false;
  }
  return !/[\s,.;!?]/.test(ch);
}

// Strip characters that can break terminal rendering
function stripUnsafeCharacters(str: string): string {
  const stripped = stripAnsi(str);
  return toCodePoints(stripped)
    .filter((char) => {
      if (char.length > 1) return false;
      const code = char.codePointAt(0);
      if (code === undefined) {
        return false;
      }
      const isUnsafe =
        code === 127 || (code <= 31 && code !== 13 && code !== 10);
      return !isUnsafe;
    })
    .join('');
}

export const GeminiInputPrompt: React.FC<GeminiInputPromptProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'Type your message...',
  focus = true,
  inputWidth = 60,
}) => {
  const [lines, setLines] = useState<string[]>(['']);
  const [cursorRow, setCursorRow] = useState(0);
  const [cursorCol, setCursorCol] = useState(0);

  // Debug log to see if component is mounting
  React.useEffect(() => {
    console.log('GeminiInputPrompt mounted:', { focus, disabled, placeholder });
  }, []);

  const getText = useCallback(() => {
    return lines.join('\n');
  }, [lines]);

  const setText = useCallback((newText: string) => {
    const newLines = newText.replace(/\r\n?/g, '\n').split('\n');
    setLines(newLines.length === 0 ? [''] : newLines);
    const lastLineIndex = newLines.length - 1;
    setCursorRow(lastLineIndex);
    setCursorCol(cpLen(newLines[lastLineIndex] || ''));
  }, []);

  const insertText = useCallback((text: string) => {
    const newLines = [...lines];
    const cleanText = stripUnsafeCharacters(text.replace(/\r\n/g, '\n').replace(/\r/g, '\n'));
    const parts = cleanText.split('\n');
    
    const currentLine = newLines[cursorRow] || '';
    const before = cpSlice(currentLine, 0, cursorCol);
    const after = cpSlice(currentLine, cursorCol);

    if (parts.length > 1) {
      // Multi-line insertion
      newLines[cursorRow] = before + parts[0];
      const remainingParts = parts.slice(1);
      const lastPart = remainingParts.pop() || '';
      newLines.splice(cursorRow + 1, 0, ...remainingParts);
      newLines.splice(cursorRow + parts.length - 1, 0, lastPart + after);
      setCursorRow(cursorRow + parts.length - 1);
      setCursorCol(cpLen(lastPart));
    } else {
      // Single line insertion
      newLines[cursorRow] = before + parts[0] + after;
      setCursorCol(cpLen(before) + cpLen(parts[0]));
    }

    setLines(newLines);
  }, [lines, cursorRow, cursorCol]);

  const backspace = useCallback(() => {
    if (cursorCol > 0) {
      // Delete character before cursor
      const newLines = [...lines];
      const currentLine = newLines[cursorRow] || '';
      const before = cpSlice(currentLine, 0, cursorCol - 1);
      const after = cpSlice(currentLine, cursorCol);
      newLines[cursorRow] = before + after;
      setLines(newLines);
      setCursorCol(cursorCol - 1);
    } else if (cursorRow > 0) {
      // Join with previous line
      const newLines = [...lines];
      const currentLine = newLines[cursorRow] || '';
      const prevLine = newLines[cursorRow - 1] || '';
      const newCol = cpLen(prevLine);
      newLines[cursorRow - 1] = prevLine + currentLine;
      newLines.splice(cursorRow, 1);
      setLines(newLines);
      setCursorRow(cursorRow - 1);
      setCursorCol(newCol);
    }
  }, [lines, cursorRow, cursorCol]);

  const deleteChar = useCallback(() => {
    const currentLine = lines[cursorRow] || '';
    if (cursorCol < cpLen(currentLine)) {
      // Delete character at cursor
      const newLines = [...lines];
      const before = cpSlice(currentLine, 0, cursorCol);
      const after = cpSlice(currentLine, cursorCol + 1);
      newLines[cursorRow] = before + after;
      setLines(newLines);
    } else if (cursorRow < lines.length - 1) {
      // Join with next line
      const newLines = [...lines];
      const nextLine = newLines[cursorRow + 1] || '';
      newLines[cursorRow] = currentLine + nextLine;
      newLines.splice(cursorRow + 1, 1);
      setLines(newLines);
    }
  }, [lines, cursorRow, cursorCol]);

  const deleteWordLeft = useCallback(() => {
    const currentLine = lines[cursorRow] || '';
    const codePoints = toCodePoints(currentLine);
    let pos = cursorCol - 1;

    // Skip whitespace
    while (pos >= 0 && !isWordChar(codePoints[pos])) {
      pos--;
    }

    // Delete word characters
    while (pos >= 0 && isWordChar(codePoints[pos])) {
      pos--;
    }

    const deleteCount = cursorCol - pos - 1;
    if (deleteCount > 0) {
      const newLines = [...lines];
      const before = cpSlice(currentLine, 0, cursorCol - deleteCount);
      const after = cpSlice(currentLine, cursorCol);
      newLines[cursorRow] = before + after;
      setLines(newLines);
      setCursorCol(cursorCol - deleteCount);
    }
  }, [lines, cursorRow, cursorCol]);

  const deleteWordRight = useCallback(() => {
    const currentLine = lines[cursorRow] || '';
    const codePoints = toCodePoints(currentLine);
    let pos = cursorCol;

    // Skip whitespace
    while (pos < codePoints.length && !isWordChar(codePoints[pos])) {
      pos++;
    }

    // Delete word characters
    while (pos < codePoints.length && isWordChar(codePoints[pos])) {
      pos++;
    }

    const deleteCount = pos - cursorCol;
    if (deleteCount > 0) {
      const newLines = [...lines];
      const before = cpSlice(currentLine, 0, cursorCol);
      const after = cpSlice(currentLine, cursorCol + deleteCount);
      newLines[cursorRow] = before + after;
      setLines(newLines);
    }
  }, [lines, cursorRow, cursorCol]);

  const moveCursor = useCallback((direction: 'left' | 'right' | 'up' | 'down' | 'wordLeft' | 'wordRight' | 'home' | 'end') => {
    switch (direction) {
      case 'left':
        if (cursorCol > 0) {
          setCursorCol(cursorCol - 1);
        } else if (cursorRow > 0) {
          setCursorRow(cursorRow - 1);
          setCursorCol(cpLen(lines[cursorRow - 1] || ''));
        }
        break;

      case 'right':
        const currentLine = lines[cursorRow] || '';
        if (cursorCol < cpLen(currentLine)) {
          setCursorCol(cursorCol + 1);
        } else if (cursorRow < lines.length - 1) {
          setCursorRow(cursorRow + 1);
          setCursorCol(0);
        }
        break;

      case 'up':
        if (cursorRow > 0) {
          const prevLine = lines[cursorRow - 1] || '';
          setCursorRow(cursorRow - 1);
          setCursorCol(Math.min(cursorCol, cpLen(prevLine)));
        }
        break;

      case 'down':
        if (cursorRow < lines.length - 1) {
          const nextLine = lines[cursorRow + 1] || '';
          setCursorRow(cursorRow + 1);
          setCursorCol(Math.min(cursorCol, cpLen(nextLine)));
        }
        break;

      case 'wordLeft': {
        const currentLine = lines[cursorRow] || '';
        const codePoints = toCodePoints(currentLine);
        let pos = cursorCol - 1;

        // Skip whitespace
        while (pos >= 0 && !isWordChar(codePoints[pos])) {
          pos--;
        }

        // Move to start of word
        while (pos >= 0 && isWordChar(codePoints[pos])) {
          pos--;
        }

        setCursorCol(Math.max(0, pos + 1));
        break;
      }

      case 'wordRight': {
        const currentLine = lines[cursorRow] || '';
        const codePoints = toCodePoints(currentLine);
        let pos = cursorCol;

        // Skip whitespace
        while (pos < codePoints.length && !isWordChar(codePoints[pos])) {
          pos++;
        }

        // Move to end of word
        while (pos < codePoints.length && isWordChar(codePoints[pos])) {
          pos++;
        }

        setCursorCol(Math.min(cpLen(currentLine), pos));
        break;
      }

      case 'home':
        setCursorCol(0);
        break;

      case 'end':
        setCursorCol(cpLen(lines[cursorRow] || ''));
        break;
    }
  }, [lines, cursorRow, cursorCol]);

  const newline = useCallback(() => {
    const newLines = [...lines];
    const currentLine = newLines[cursorRow] || '';
    const before = cpSlice(currentLine, 0, cursorCol);
    const after = cpSlice(currentLine, cursorCol);
    
    newLines[cursorRow] = before;
    newLines.splice(cursorRow + 1, 0, after);
    setLines(newLines);
    setCursorRow(cursorRow + 1);
    setCursorCol(0);
  }, [lines, cursorRow, cursorCol]);

  const killLineRight = useCallback(() => {
    const newLines = [...lines];
    const currentLine = newLines[cursorRow] || '';
    const before = cpSlice(currentLine, 0, cursorCol);
    newLines[cursorRow] = before;
    setLines(newLines);
  }, [lines, cursorRow, cursorCol]);

  const killLineLeft = useCallback(() => {
    const newLines = [...lines];
    const currentLine = newLines[cursorRow] || '';
    const after = cpSlice(currentLine, cursorCol);
    newLines[cursorRow] = after;
    setLines(newLines);
    setCursorCol(0);
  }, [lines, cursorRow, cursorCol]);

  const handleSubmit = useCallback(() => {
    const text = getText().trim();
    if (text) {
      onSubmit(text);
      setText('');
    }
  }, [getText, onSubmit, setText]);

  const handleInput = useCallback((key: Key) => {
    console.log('GeminiInputPrompt handleInput received:', key);
    if (!focus || disabled) {
      console.log('GeminiInputPrompt handleInput skipped:', { focus, disabled });
      return;
    }

    // Handle submission
    if (key.name === 'return' && !key.ctrl && !key.meta && !key.paste) {
      const currentLine = lines[cursorRow] || '';
      const charBefore = cursorCol > 0 ? cpSlice(currentLine, cursorCol - 1, cursorCol) : '';
      if (charBefore === '\\') {
        backspace();
        newline();
      } else {
        handleSubmit();
      }
      return;
    }

    // Multi-line newline
    if (key.name === 'return' && (key.ctrl || key.meta || key.paste)) {
      newline();
      return;
    }

    // Navigation
    if (key.name === 'left') {
      moveCursor(key.meta ? 'wordLeft' : 'left');
      return;
    }
    if (key.name === 'right') {
      moveCursor(key.meta ? 'wordRight' : 'right');
      return;
    }
    if (key.name === 'up') {
      moveCursor('up');
      return;
    }
    if (key.name === 'down') {
      moveCursor('down');
      return;
    }

    // Home/End
    if (key.ctrl && key.name === 'a') {
      moveCursor('home');
      return;
    }
    if (key.ctrl && key.name === 'e') {
      moveCursor('end');
      return;
    }

    // Deletion
    if (key.name === 'backspace') {
      if (key.meta) {
        deleteWordLeft();
      } else {
        backspace();
      }
      return;
    }
    if (key.name === 'delete') {
      if (key.meta) {
        deleteWordRight();
      } else {
        deleteChar();
      }
      return;
    }

    // Kill line commands
    if (key.ctrl && key.name === 'k') {
      killLineRight();
      return;
    }
    if (key.ctrl && key.name === 'u') {
      killLineLeft();
      return;
    }

    // Clear all
    if (key.ctrl && key.name === 'l') {
      setText('');
      return;
    }

    // Handle paste
    if (key.paste && key.sequence) {
      insertText(key.sequence);
      return;
    }

    // Regular character input
    if (key.sequence && key.sequence.length === 1 && !key.ctrl) {
      const char = key.sequence;
      const charCode = char.charCodeAt(0);
      if (charCode >= 32 || charCode === 9) { // Printable chars and tab
        insertText(char);
      }
      return;
    }
  }, [
    focus, disabled, lines, cursorRow, cursorCol, backspace, newline, 
    handleSubmit, moveCursor, deleteWordLeft, deleteWordRight, deleteChar,
    killLineRight, killLineLeft, setText, insertText
  ]);

  useKeypress(handleInput, { isActive: focus && !disabled });

  // Render the input
  const isMultiline = lines.length > 1;
  const text = getText();

  const renderSingleLine = () => {
    const currentLine = lines[0] || '';
    const displayText = currentLine || placeholder;
    const isPlaceholder = !currentLine;

    if (disabled || !focus) {
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

    const beforeCursor = cpSlice(currentLine, 0, cursorCol);
    const atCursor = cpSlice(currentLine, cursorCol, cursorCol + 1) || ' ';
    const afterCursor = cpSlice(currentLine, cursorCol + 1);

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
        <Text color="cyan">┌─ multiline ─ {lines.length} lines, {text.length} chars ─┐</Text>
        {lines.slice(0, 6).map((line, lineIndex) => {
          const isCurrentLine = lineIndex === cursorRow;
          
          if (isCurrentLine && focus && !disabled) {
            const beforeCursor = cpSlice(line, 0, cursorCol);
            const atCursor = cpSlice(line, cursorCol, cursorCol + 1) || ' ';
            const afterCursor = cpSlice(line, cursorCol + 1);
            
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
                  {line || (lineIndex === 0 && !text ? placeholder : '')}
                </Text>
              </Box>
            );
          }
        })}
        {lines.length > 6 && (
          <Box>
            <Text color="cyan">│ </Text>
            <Text color="gray">... {lines.length - 6} more lines</Text>
          </Box>
        )}
        <Text color="cyan">└{'─'.repeat(50)}┘</Text>
      </Box>
    );
  };

  return (
    <Box flexDirection="column" marginY={1}>
      {isMultiline ? renderMultiline() : renderSingleLine()}
      
      {focus && !disabled && (
        <Box marginTop={1}>
          <Text color="gray">
            {isMultiline 
              ? 'Ctrl+Enter: Send • Enter: New line • Meta+←/→: Word jump • Meta+Backspace: Delete word'
              : 'Enter: Send • Ctrl+Enter: New line • Meta+←/→: Word jump'
            }
          </Text>
        </Box>
      )}
    </Box>
  );
};