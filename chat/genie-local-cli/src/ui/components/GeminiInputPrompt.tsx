/**
 * Gemini-style InputPrompt component that uses the visual design from gemini-cli
 * but connects to genie's backend functionality
 */

import React, { useCallback } from 'react';
import { Box, Text, useInput, type Key as InkKeyType } from 'ink';
import { Colors } from '../colors.js';
import { TextBuffer } from './shared/text-buffer.js';
import { cpSlice, cpLen } from '../utils/textUtils.js';
import chalk from 'chalk';
import stringWidth from 'string-width';

export interface GeminiInputPromptProps {
  buffer: TextBuffer;
  onSubmit: (value: string) => void;
  onClearScreen: () => void;
  placeholder?: string;
  focus?: boolean;
  inputWidth: number;
  shellModeActive?: boolean;
  isActive: boolean;
}

export const GeminiInputPrompt: React.FC<GeminiInputPromptProps> = ({
  buffer,
  onSubmit,
  onClearScreen,
  placeholder = '  Type your message...',
  focus = true,
  inputWidth,
  shellModeActive = false,
  isActive = true,
}) => {
  const handleSubmitAndClear = useCallback(
    (submittedValue: string) => {
      // Clear the buffer *before* calling onSubmit
      buffer.setText('');
      onSubmit(submittedValue);
    },
    [onSubmit, buffer],
  );

  useInput((input: string, key: InkKeyType) => {
    if (!focus || !isActive) {
      return;
    }

    if (key.ctrl && input === 'l') {
      onClearScreen();
      return;
    }

    if (input === '\r' && !key.ctrl && !key.meta) {
      if (buffer.text.trim()) {
        const [row, col] = buffer.cursor;
        const line = buffer.lines[row];
        const charBefore = col > 0 ? cpSlice(line, col - 1, col) : '';
        if (charBefore === '\\') {
          buffer.backspace();
          buffer.newline();
        } else {
          handleSubmitAndClear(buffer.text);
        }
      }
      return;
    }

    // Newline insertion
    if (input === '\r' && (key.ctrl || key.meta)) {
      buffer.newline();
      return;
    }

    // Ctrl+A (Home) / Ctrl+E (End)
    if (key.ctrl && input === 'a') {
      buffer.move('home');
      return;
    }
    if (key.ctrl && input === 'e') {
      buffer.move('end');
      return;
    }

    // Kill line commands
    if (key.ctrl && input === 'k') {
      buffer.killLineRight();
      return;
    }
    if (key.ctrl && input === 'u') {
      buffer.killLineLeft();
      return;
    }

    // Try to handle the input with the text buffer
    try {
      // Create a pseudo-key object that the text buffer can handle
      const pseudoKey = {
        name: input === '\r' ? 'return' : input,
        ctrl: key.ctrl || false,
        meta: key.meta || false,
        shift: key.shift || false,
        paste: false,
        sequence: input
      };
      buffer.handleInput(pseudoKey);
    } catch (error) {
      // If the text buffer can't handle it, fallback to simple text insertion
      if (input.length === 1 && !key.ctrl && !key.meta) {
        buffer.insert(input);
      }
    }
  }, {
    isActive: focus && isActive
  });

  const linesToRender = buffer.viewportVisualLines;
  const [cursorVisualRowAbsolute, cursorVisualColAbsolute] = buffer.visualCursor;
  const scrollVisualRow = buffer.visualScrollRow;

  return (
    <Box
      borderStyle="round"
      borderColor={shellModeActive ? Colors.AccentYellow : Colors.AccentBlue}
      paddingX={1}
    >
      <Text
        color={shellModeActive ? Colors.AccentYellow : Colors.AccentPurple}
      >
        {shellModeActive ? '! ' : '> '}
      </Text>
      <Box flexGrow={1} flexDirection="column">
        {buffer.text.length === 0 && placeholder ? (
          focus ? (
            <Text>
              {chalk.inverse(placeholder.slice(0, 1))}
              <Text color={Colors.Gray}>{placeholder.slice(1)}</Text>
            </Text>
          ) : (
            <Text color={Colors.Gray}>{placeholder}</Text>
          )
        ) : (
          linesToRender.map((lineText, visualIdxInRenderedSet) => {
            const cursorVisualRow = cursorVisualRowAbsolute - scrollVisualRow;
            let display = cpSlice(lineText, 0, inputWidth);
            const currentVisualWidth = stringWidth(display);
            if (currentVisualWidth < inputWidth) {
              display = display + ' '.repeat(inputWidth - currentVisualWidth);
            }

            if (visualIdxInRenderedSet === cursorVisualRow) {
              const relativeVisualColForHighlight = cursorVisualColAbsolute;

              if (relativeVisualColForHighlight >= 0) {
                if (relativeVisualColForHighlight < cpLen(display)) {
                  const charToHighlight =
                    cpSlice(
                      display,
                      relativeVisualColForHighlight,
                      relativeVisualColForHighlight + 1,
                    ) || ' ';
                  const highlighted = chalk.inverse(charToHighlight);
                  display =
                    cpSlice(display, 0, relativeVisualColForHighlight) +
                    highlighted +
                    cpSlice(display, relativeVisualColForHighlight + 1);
                } else if (
                  relativeVisualColForHighlight === cpLen(display) &&
                  cpLen(display) === inputWidth
                ) {
                  display = display + chalk.inverse(' ');
                }
              }
            }
            return (
              <Text key={`line-${visualIdxInRenderedSet}`}>{display}</Text>
            );
          })
        )}
      </Box>
    </Box>
  );
};