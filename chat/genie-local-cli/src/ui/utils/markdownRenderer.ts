/**
 * Markdown renderer for terminal display using ink components
 */

import React from 'react';
import { Box, Text } from 'ink';
import { Colors } from '../colors.js';

export interface MarkdownToken {
  type: 'heading' | 'paragraph' | 'code_block' | 'inline_code' | 'list_item' | 'bold' | 'italic' | 'link' | 'text' | 'line_break';
  content: string;
  level?: number; // For headings
  language?: string; // For code blocks
  url?: string; // For links
}

export class MarkdownRenderer {
  static parseMarkdown(text: string): MarkdownToken[] {
    const tokens: MarkdownToken[] = [];
    const lines = text.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Empty line
      if (line.trim() === '') {
        tokens.push({ type: 'line_break', content: '' });
        continue;
      }
      
      // Headings
      const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
      if (headingMatch) {
        tokens.push({
          type: 'heading',
          content: headingMatch[2],
          level: headingMatch[1].length,
        });
        continue;
      }
      
      // Code blocks
      if (line.startsWith('```')) {
        const language = line.substring(3).trim();
        const codeLines: string[] = [];
        i++; // Skip the opening ```
        
        while (i < lines.length && !lines[i].startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        
        tokens.push({
          type: 'code_block',
          content: codeLines.join('\n'),
          language: language || 'text',
        });
        continue;
      }
      
      // List items
      if (line.match(/^\s*[-*+]\s+/)) {
        const content = line.replace(/^\s*[-*+]\s+/, '');
        tokens.push({
          type: 'list_item',
          content: content,
        });
        continue;
      }
      
      // Regular paragraph with inline formatting
      tokens.push(...this.parseInlineFormatting(line));
    }
    
    return tokens;
  }
  
  private static parseInlineFormatting(text: string): MarkdownToken[] {
    const tokens: MarkdownToken[] = [];
    let currentText = text;
    
    // Simple regex patterns for inline formatting
    const patterns = [
      { regex: /`([^`]+)`/g, type: 'inline_code' as const },
      { regex: /\*\*([^*]+)\*\*/g, type: 'bold' as const },
      { regex: /\*([^*]+)\*/g, type: 'italic' as const },
      { regex: /\[([^\]]+)\]\(([^)]+)\)/g, type: 'link' as const },
    ];
    
    let hasFormatting = false;
    for (const pattern of patterns) {
      if (pattern.regex.test(currentText)) {
        hasFormatting = true;
        break;
      }
    }
    
    if (!hasFormatting) {
      tokens.push({ type: 'paragraph', content: currentText });
      return tokens;
    }
    
    // For now, treat as paragraph and let the renderer handle inline formatting
    tokens.push({ type: 'paragraph', content: currentText });
    return tokens;
  }
  
  static renderToReact(tokens: MarkdownToken[]): React.ReactElement {
    const elements: React.ReactElement[] = [];
    
    tokens.forEach((token, index) => {
      switch (token.type) {
        case 'heading':
          elements.push(
            React.createElement(Box, { key: index, marginY: 1 },
              React.createElement(Text, {
                color: Colors.AccentBlue,
                bold: true,
                underline: token.level === 1,
              }, `${'#'.repeat(token.level || 1)} ${token.content}`)
            )
          );
          break;
          
        case 'paragraph':
          elements.push(
            React.createElement(Box, { key: index, marginBottom: 1 },
              React.createElement(Text, {
                color: Colors.Foreground,
              }, this.renderInlineFormatting(token.content))
            )
          );
          break;
          
        case 'code_block':
          elements.push(
            React.createElement(Box, {
              key: index,
              borderStyle: 'round',
              borderColor: Colors.Gray,
              paddingX: 1,
              marginY: 1,
            },
              React.createElement(Text, {
                color: Colors.AccentGreen,
                backgroundColor: Colors.Background,
              }, token.content)
            )
          );
          break;
          
        case 'inline_code':
          elements.push(
            React.createElement(Text, {
              key: index,
              color: Colors.AccentGreen,
              backgroundColor: Colors.Gray,
            }, token.content)
          );
          break;
          
        case 'list_item':
          elements.push(
            React.createElement(Box, { key: index, marginLeft: 2 },
              React.createElement(Text, {
                color: Colors.AccentYellow,
              }, '• '),
              React.createElement(Text, {
                color: Colors.Foreground,
              }, token.content)
            )
          );
          break;
          
        case 'line_break':
          elements.push(
            React.createElement(Box, { key: index, height: 1 })
          );
          break;
          
        default:
          elements.push(
            React.createElement(Text, {
              key: index,
              color: Colors.Foreground,
            }, token.content)
          );
      }
    });
    
    return React.createElement(Box, { flexDirection: 'column' }, ...elements);
  }
  
  private static renderInlineFormatting(text: string): React.ReactElement[] {
    const elements: React.ReactElement[] = [];
    let currentText = text;
    let elementIndex = 0;
    
    // Handle inline code
    const codeRegex = /`([^`]+)`/g;
    let lastIndex = 0;
    let match;
    
    while ((match = codeRegex.exec(currentText)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const beforeText = currentText.substring(lastIndex, match.index);
        if (beforeText) {
          elements.push(
            React.createElement(Text, { key: elementIndex++ }, beforeText)
          );
        }
      }
      
      // Add the code element
      elements.push(
        React.createElement(Text, {
          key: elementIndex++,
          color: Colors.AccentGreen,
          backgroundColor: Colors.Gray,
        }, match[1])
      );
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < currentText.length) {
      const remainingText = currentText.substring(lastIndex);
      if (remainingText) {
        elements.push(
          React.createElement(Text, { key: elementIndex++ }, remainingText)
        );
      }
    }
    
    // If no inline formatting found, return the original text
    if (elements.length === 0) {
      elements.push(
        React.createElement(Text, { key: 0 }, currentText)
      );
    }
    
    return elements;
  }
}

export const renderMarkdown = (text: string): React.ReactElement => {
  const tokens = MarkdownRenderer.parseMarkdown(text);
  return MarkdownRenderer.renderToReact(tokens);
};