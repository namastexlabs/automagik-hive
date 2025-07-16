/**
 * History item display component adapted from gemini-cli for genie context
 */

import React from 'react';
import { Box, Text } from 'ink';
import { Colors } from '../colors.js';
import { HistoryItem, MessageType } from '../types.js';
import { MarkdownText } from './MarkdownText.js';

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
      case MessageType.TEAM_START:
        return Colors.AccentBlue;
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
      case MessageType.TEAM_START:
        return '🔵 ';
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
              {typeof tool.tool_result === 'string' ? (
                <MarkdownText color={Colors.Gray}>{tool.tool_result}</MarkdownText>
              ) : (
                <Text color={Colors.Gray}>{JSON.stringify(tool.tool_result, null, 2)}</Text>
              )}
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
          flexDirection="column"
        >
          <Text color={getMessageColor(item.type)}>
            {item.text}
          </Text>
          {/* Display rich tool metadata with improved alignment */}
          {item.metadata?.tool && (
            <Box marginTop={1} flexDirection="column">
              {item.metadata.tool.tool_call_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentCyan} bold>Tool Call ID:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.tool.tool_call_id}</Text>
                </Box>
              )}
              {item.metadata.tool.agent_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentCyan} bold>Agent:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.tool.agent_name || item.metadata.tool.agent_id}</Text>
                </Box>
              )}
              {item.metadata.tool.run_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentCyan} bold>Run ID:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.tool.run_id}</Text>
                </Box>
              )}
              {item.metadata.tool.created_at && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentCyan} bold>Created:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{new Date(item.metadata.tool.created_at).toLocaleTimeString()}</Text>
                </Box>
              )}
              {item.metadata.tool.tool_call_error && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentRed} bold>Error:</Text>
                  </Box>
                  <Text color={Colors.AccentRed}>{item.metadata.tool.tool_call_error}</Text>
                </Box>
              )}
            </Box>
          )}
          {renderRichToolData()}
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
          flexDirection="column"
        >
          <Text color={getMessageColor(item.type)}>
            {item.text}
          </Text>
          {/* Display rich agent metadata with improved alignment */}
          {item.metadata?.agent && (
            <Box marginTop={1} flexDirection="column">
              {item.metadata.agent.agent_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={18}>
                    <Text color={Colors.AccentCyan} bold>Agent ID:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.agent.agent_id}</Text>
                </Box>
              )}
              {item.metadata.agent.run_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={18}>
                    <Text color={Colors.AccentCyan} bold>Run ID:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.agent.run_id}</Text>
                </Box>
              )}
              {item.metadata.agent.session_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={18}>
                    <Text color={Colors.AccentCyan} bold>Session ID:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.agent.session_id}</Text>
                </Box>
              )}
              {item.metadata.agent.team_session_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={18}>
                    <Text color={Colors.AccentCyan} bold>Team Session ID:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.agent.team_session_id}</Text>
                </Box>
              )}
              {item.metadata.agent.model && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={18}>
                    <Text color={Colors.AccentCyan} bold>Model:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.agent.model_provider || 'unknown'}/{item.metadata.agent.model}</Text>
                </Box>
              )}
            </Box>
          )}
        </Box>
      );
    }

    // Special rendering for team start events
    if (item.type === MessageType.TEAM_START) {
      return (
        <Box
          borderStyle="round"
          borderColor={Colors.AccentBlue}
          paddingX={1}
          marginY={1}
          flexDirection="column"
        >
          <Text color={getMessageColor(item.type)}>
            {item.text}
          </Text>
          {/* Display rich team metadata with improved alignment */}
          {item.metadata?.team && (
            <Box marginTop={1} flexDirection="column">
              {item.metadata.team.team_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentBlue} bold>Team ID:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.team.team_id}</Text>
                </Box>
              )}
              {item.metadata.team.team_name && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentBlue} bold>Team Name:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.team.team_name}</Text>
                </Box>
              )}
              {item.metadata.team.run_id && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentBlue} bold>Run ID:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.team.run_id}</Text>
                </Box>
              )}
              {item.metadata.team.model && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentBlue} bold>Model:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.team.model_provider || 'unknown'}/{item.metadata.team.model}</Text>
                </Box>
              )}
              {item.metadata.team.mode && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={15}>
                    <Text color={Colors.AccentBlue} bold>Mode:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.team.mode}</Text>
                </Box>
              )}
            </Box>
          )}
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
              <Box marginLeft={2}>
                <MarkdownText color={Colors.Gray}>{item.metadata.thinking.reasoning}</MarkdownText>
              </Box>
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
          flexDirection="column"
        >
          <Text color={getMessageColor(item.type)} bold>
            {item.text}
          </Text>
          {item.metadata?.memory && (
            <Box marginTop={1} flexDirection="column">
              {item.metadata.memory.type && (
                <Box marginBottom={1} flexDirection="row">
                  <Box minWidth={12}>
                    <Text color={Colors.AccentPurple} bold>Type:</Text>
                  </Box>
                  <Text color={Colors.Gray}>{item.metadata.memory.type}</Text>
                </Box>
              )}
              {item.metadata.memory.content && (
                <Box marginBottom={1} flexDirection="column">
                  <Box marginBottom={1}>
                    <Text color={Colors.AccentPurple} bold>Content:</Text>
                  </Box>
                  <Box marginLeft={2}>
                    <MarkdownText color={Colors.Gray}>{item.metadata.memory.content}</MarkdownText>
                  </Box>
                </Box>
              )}
              {item.metadata.memory.metadata && (
                <Box flexDirection="column">
                  <Box marginBottom={1}>
                    <Text color={Colors.AccentPurple} bold>Metadata:</Text>
                  </Box>
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
      // Use markdown rendering for assistant responses
      if (item.type === MessageType.ASSISTANT) {
        return (
          <MarkdownText color={getMessageColor(item.type)}>
            {item.text}
          </MarkdownText>
        );
      }
      
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