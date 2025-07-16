/**
 * Markdown text component for rendering markdown in terminal
 */

import React from 'react';
import { Box, Text } from 'ink';
import { marked } from 'marked';
import { Colors } from '../colors.js';

interface MarkdownTextProps {
  children: string;
  color?: string;
}

export const MarkdownText: React.FC<MarkdownTextProps> = ({ 
  children, 
  color = Colors.Foreground 
}) => {
  try {
    // Parse markdown to tokens
    const tokens = marked.lexer(children);
    
    return (
      <Box flexDirection="column">
        {tokens.map((token, index) => renderToken(token, index, color))}
      </Box>
    );
  } catch (error) {
    // Fallback to plain text if markdown parsing fails
    console.warn('Markdown parsing failed:', error);
    return (
      <Text color={color}>
        {children}
      </Text>
    );
  }
};

const renderToken = (token: any, index: number, color: string): React.ReactElement => {
  switch (token.type) {
    case 'heading':
      return (
        <Box key={index} marginY={token.depth === 1 ? 1 : 0}>
          <Text 
            color={Colors.AccentBlue} 
            bold={true}
            underline={token.depth === 1}
          >
            {'#'.repeat(token.depth)} {token.text}
          </Text>
        </Box>
      );
      
    case 'paragraph':
      return (
        <Box key={index} marginBottom={1}>
          <Text color={color}>
            {renderInlineTokens(token.tokens || [token.text], index)}
          </Text>
        </Box>
      );
      
    case 'code':
      return (
        <Box 
          key={index}
          borderStyle="round" 
          borderColor={Colors.AccentGreen}
          paddingX={1}
          marginY={1}
        >
          <Box flexDirection="column">
            <Text color={Colors.AccentGreen} bold>
              {token.lang || 'code'}
            </Text>
            <Text color={Colors.AccentGreen}>
              {token.text}
            </Text>
          </Box>
        </Box>
      );
      
    case 'list':
      return (
        <Box key={index} flexDirection="column" marginY={1}>
          {token.items.map((item: any, itemIndex: number) => (
            <Box key={itemIndex} marginLeft={2}>
              <Text color={Colors.AccentYellow}>• </Text>
              <Text color={color}>
                {renderInlineTokens(item.tokens || [item.text], itemIndex)}
              </Text>
            </Box>
          ))}
        </Box>
      );
      
    case 'blockquote':
      return (
        <Box key={index} marginY={1} marginLeft={2}>
          <Text color={Colors.Gray}>
            {token.tokens ? renderInlineTokens(token.tokens, index) : `> ${token.text}`}
          </Text>
        </Box>
      );
      
    case 'space':
      return <Box key={index} height={1} />;
      
    default:
      return (
        <Box key={index} marginBottom={1}>
          <Text color={color}>
            {token.text || token.raw || ''}
          </Text>
        </Box>
      );
  }
};

const renderInlineTokens = (tokens: any[] | string, parentIndex: number): React.ReactElement[] => {
  if (typeof tokens === 'string') {
    return [<Text key={`${parentIndex}-text`}>{tokens}</Text>];
  }
  
  return tokens.map((token, index) => {
    const key = `${parentIndex}-${index}`;
    
    switch (token.type) {
      case 'strong':
        return (
          <Text key={key} bold>
            {token.text}
          </Text>
        );
        
      case 'em':
        return (
          <Text key={key} italic>
            {token.text}
          </Text>
        );
        
      case 'codespan':
        return (
          <Text 
            key={key}
            color={Colors.AccentGreen}
            backgroundColor={Colors.Gray}
            bold
          >
            {token.text}
          </Text>
        );
        
      case 'link':
        return (
          <Text 
            key={key}
            color={Colors.AccentCyan}
            underline
          >
            {token.text}
          </Text>
        );
        
      case 'text':
      default:
        return (
          <Text key={key}>
            {token.text || token.raw || ''}
          </Text>
        );
    }
  });
};