/**
 * History item display component adapted from gemini-cli for genie context
 */

import React from 'react';
import { Box, Text } from 'ink';
import { Colors } from '../colors.js';
import { HistoryItem, MessageType } from '../types.js';

interface HistoryItemDisplayProps {
  item: HistoryItem;
  isPending?: boolean;
  isFocused?: boolean;
  terminalWidth: number;
  availableTerminalHeight?: number;
}

export const HistoryItemDisplay: React.FC<HistoryItemDisplayProps> = ({
  item,
  isPending = false,
  isFocused = true,
  terminalWidth,
  availableTerminalHeight,
}) => {
  const getMessageColor = (type: MessageType): string => {
    switch (type) {
      case MessageType.USER:
        return Colors.AccentBlue;
      case MessageType.ASSISTANT:
        return Colors.Foreground;
      case MessageType.THINKING:
        return Colors.AccentPurple;
      case MessageType.TOOL_START:
        return Colors.AccentYellow;
      case MessageType.TOOL_COMPLETE:
        return Colors.AccentGreen;
      case MessageType.AGENT_START:
        return Colors.AccentCyan;
      case MessageType.ERROR:
        return Colors.AccentRed;
      case MessageType.INFO:
        return Colors.AccentCyan;
      case MessageType.SYSTEM:
        return Colors.AccentYellow;
      default:
        return Colors.Foreground;
    }
  };

  const getMessagePrefix = (type: MessageType): string => {
    switch (type) {
      case MessageType.USER:
        return '🧞 ';
      case MessageType.ASSISTANT:
        return '✨ ';
      case MessageType.THINKING:
        return '🤔 ';
      case MessageType.TOOL_START:
        return '🔧 ';
      case MessageType.TOOL_COMPLETE:
        return '✅ ';
      case MessageType.AGENT_START:
        return '🤖 ';
      case MessageType.ERROR:
        return '❌ ';
      case MessageType.INFO:
        return 'ℹ️  ';
      case MessageType.SYSTEM:
        return '⚙️  ';
      default:
        return '';
    }
  };

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const renderRichToolData = () => {
    const tool = item.metadata?.tool;
    if (!tool) return null;

    return (
      <Box flexDirection="column" marginTop={1}>
        {tool.tool_args && Object.keys(tool.tool_args).length > 0 && (
          <Box marginBottom={1}>
            <Text color={Colors.AccentCyan} bold>Arguments:</Text>
            <Box marginLeft={2}>
              <Text color={Colors.Gray}>{JSON.stringify(tool.tool_args, null, 2)}</Text>
            </Box>
          </Box>
        )}
        {tool.tool_result && (
          <Box marginBottom={1}>
            <Text color={Colors.AccentGreen} bold>Result:</Text>
            <Box marginLeft={2}>
              <Text color={Colors.Gray}>{typeof tool.tool_result === 'string' ? tool.tool_result : JSON.stringify(tool.tool_result, null, 2)}</Text>
            </Box>
          </Box>
        )}
        {tool.metrics && (
          <Box>
            <Text color={Colors.AccentPurple} bold>Metrics:</Text>
            <Box marginLeft={2}>
              <Text color={Colors.Gray}>{tool.metrics.time ? `⏱️ ${(tool.metrics.time * 1000).toFixed(0)}ms` : ''} {tool.metrics.tokens ? `🔤 ${tool.metrics.tokens} tokens` : ''}</Text>
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  const renderRAGData = () => {
    const rag = item.metadata?.rag;
    if (!rag) return null;

    return (
      <Box flexDirection="column" marginTop={1}>
        {rag.query && (
          <Box marginBottom={1}>
            <Text color={Colors.AccentCyan} bold>Query:</Text>
            <Box marginLeft={2}>
              <Text color={Colors.Gray}>{rag.query}</Text>
            </Box>
          </Box>
        )}
        {rag.results && rag.results.length > 0 && (
          <Box marginBottom={1}>
            <Text color={Colors.AccentGreen} bold>Results:</Text>
            <Box marginLeft={2}>
              <Text color={Colors.Gray}>{rag.results.length} matches found</Text>
            </Box>
          </Box>
        )}
        {rag.metadata && (
          <Box>
            <Text color={Colors.AccentPurple} bold>Metadata:</Text>
            <Box marginLeft={2}>
              <Text color={Colors.Gray}>{JSON.stringify(rag.metadata, null, 2)}</Text>
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  const renderMessageContent = () => {
    // Special rendering for tool events
    if (item.type === MessageType.TOOL_START || item.type === MessageType.TOOL_COMPLETE) {
      return (
        <Box
          borderStyle="round"
          borderColor={item.type === MessageType.TOOL_START ? Colors.AccentYellow : Colors.AccentGreen}
          paddingX={1}
          marginY={1}
        >
          <Text color={getMessageColor(item.type)}>
            {item.text}
          </Text>
        </Box>
      );
    }

    // Special rendering for agent events
    if (item.type === MessageType.AGENT_START) {
      return (
        <Box
          borderStyle="round"
          borderColor={Colors.AccentCyan}
          paddingX={1}
          marginY={1}
        >
          <Text color={getMessageColor(item.type)}>
            {item.text}
          </Text>
        </Box>
      );
    }

    // Special rendering for thinking events
    if (item.type === MessageType.THINKING) {
      return (
        <Box
          borderStyle="round"
          borderColor={Colors.AccentPurple}
          paddingX={1}
          marginY={1}
        >
          <Text color={getMessageColor(item.type)} italic>
            {item.text}
          </Text>
          {item.metadata?.thinking && item.metadata.thinking.reasoning && (
            <Box marginTop={1}>
              <Text color={Colors.AccentPurple} bold>Reasoning:</Text>
              <Text color={Colors.Gray} italic> {item.metadata.thinking.reasoning}</Text>
            </Box>
          )}
        </Box>
      );
    }

    // Special rendering for memory events
    if (item.type === MessageType.MEMORY_UPDATE) {
      return (
        <Box
          borderStyle="round"
          borderColor={Colors.AccentPurple}
          paddingX={1}
          marginY={1}
        >
          <Text color={getMessageColor(item.type)} bold>
            {item.text}
          </Text>
          {item.metadata?.memory && (
            <Box marginTop={1}>
              {item.metadata.memory.type && (
                <Box marginBottom={1}>
                  <Text color={Colors.AccentPurple} bold>Type:</Text>
                  <Box marginLeft={2}>
                    <Text color={Colors.Gray}>{item.metadata.memory.type}</Text>
                  </Box>
                </Box>
              )}
              {item.metadata.memory.content && (
                <Box marginBottom={1}>
                  <Text color={Colors.AccentPurple} bold>Content:</Text>
                  <Box marginLeft={2}>
                    <Text color={Colors.Gray}>{item.metadata.memory.content}</Text>
                  </Box>
                </Box>
              )}
              {item.metadata.memory.metadata && (
                <Box>
                  <Text color={Colors.AccentPurple} bold>Metadata:</Text>
                  <Box marginLeft={2}>
                    <Text color={Colors.Gray}>{JSON.stringify(item.metadata.memory.metadata, null, 2)}</Text>
                  </Box>
                </Box>
              )}
            </Box>
          )}
        </Box>
      );
    }

    // For simple text content
    if (typeof item.text === 'string') {
      return (
        <Text color={getMessageColor(item.type)}>
          {item.text}
        </Text>
      );
    }

    // For more complex content (could be extended in the future)
    return (
      <Text color={getMessageColor(item.type)}>
        {JSON.stringify(item.text)}
      </Text>
    );
  };

  const maxWidth = Math.floor(terminalWidth * 0.9);

  return (
    <Box
      flexDirection="column"
      marginBottom={1}
      width={maxWidth}
      minHeight={availableTerminalHeight ? 1 : undefined}
    >
      {/* Message header with type indicator and timestamp */}
      <Box justifyContent="space-between" marginBottom={0}>
        <Box>
          <Text color={getMessageColor(item.type)} bold>
            {getMessagePrefix(item.type)}
            {item.type === MessageType.USER ? 'You' : 
             item.type === MessageType.ASSISTANT ? (item.metadata?.target?.name || item.metadata?.target?.id || 'Genie') :
             item.type.charAt(0).toUpperCase() + item.type.slice(1).replace('_', ' ')}
          </Text>
          {isPending && (
            <Text color={Colors.AccentYellow} italic> (processing...)</Text>
          )}
        </Box>
        
        {item.timestamp && (
          <Text color={Colors.Gray} dimColor>
            {formatTimestamp(item.timestamp)}
          </Text>
        )}
      </Box>

      {/* Message content */}
      <Box 
        marginLeft={2}
        flexDirection="column"
        width="100%"
      >
        {renderMessageContent()}
      </Box>

      {/* Error details for error messages */}
      {item.type === MessageType.ERROR && item.details && (
        <Box 
          marginLeft={2} 
          marginTop={1}
          borderStyle="round"
          borderColor={Colors.AccentRed}
          paddingX={1}
        >
          <Text color={Colors.Gray} italic>
            {item.details}
          </Text>
        </Box>
      )}
    </Box>
  );
};