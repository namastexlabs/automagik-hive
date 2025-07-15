import React from 'react';
import { Box, Text } from 'ink';
import { HistoryItem, MessageType } from '../types.js';

interface ChatDisplayProps {
  history: HistoryItem[];
  pendingMessage: HistoryItem | null;
  terminalWidth: number;
  terminalHeight: number;
}

export const ChatDisplay: React.FC<ChatDisplayProps> = ({
  history,
  pendingMessage,
  terminalWidth,
  terminalHeight,
}) => {
  const maxWidth = Math.min(terminalWidth - 4, 120);
  const maxHeight = Math.max(terminalHeight - 15, 10); // Reserve space for header/footer

  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getMessageColor = (type: MessageType): string => {
    switch (type) {
      case MessageType.USER:
        return 'blue';
      case MessageType.ASSISTANT:
        return 'green';
      case MessageType.THINKING:
        return 'cyan';
      case MessageType.TOOL_START:
        return 'yellow';
      case MessageType.TOOL_COMPLETE:
        return 'green';
      case MessageType.AGENT_START:
        return 'magenta';
      case MessageType.ERROR:
        return 'red';
      case MessageType.INFO:
        return 'yellow';
      case MessageType.SYSTEM:
        return 'gray';
      default:
        return 'white';
    }
  };

  const getMessagePrefix = (type: MessageType): string => {
    switch (type) {
      case MessageType.USER:
        return '👤 You';
      case MessageType.ASSISTANT:
        return '🤖 Assistant';
      case MessageType.THINKING:
        return '💭 Thinking';
      case MessageType.TOOL_START:
        return '🔧 Tool';
      case MessageType.TOOL_COMPLETE:
        return '✅ Tool';
      case MessageType.AGENT_START:
        return '🚀 Agent';
      case MessageType.ERROR:
        return '❌ Error';
      case MessageType.INFO:
        return 'ℹ️  Info';
      case MessageType.SYSTEM:
        return '⚙️  System';
      default:
        return '• ';
    }
  };

  const wrapText = (text: string, width: number): string[] => {
    const words = text.split(' ');
    const lines: string[] = [];
    let currentLine = '';

    for (const word of words) {
      if (currentLine.length + word.length + 1 <= width) {
        currentLine += (currentLine ? ' ' : '') + word;
      } else {
        if (currentLine) {
          lines.push(currentLine);
        }
        currentLine = word;
      }
    }

    if (currentLine) {
      lines.push(currentLine);
    }

    return lines.length > 0 ? lines : [''];
  };

  const isCompactMessage = (type: MessageType): boolean => {
    return [
      MessageType.THINKING,
      MessageType.TOOL_START,
      MessageType.TOOL_COMPLETE,
      MessageType.AGENT_START
    ].includes(type);
  };

  const renderMessage = (message: HistoryItem, isPending: boolean = false) => {
    const color = getMessageColor(message.type);
    const prefix = getMessagePrefix(message.type);
    const timestamp = formatTimestamp(message.timestamp);
    const isCompact = isCompactMessage(message.type);
    
    // For compact messages (thinking, tools), show inline
    if (isCompact && !isPending) {
      return (
        <Box key={message.id} marginY={0}>
          <Text color={color} dimColor>
            {prefix}: {message.text}
          </Text>
        </Box>
      );
    }

    // For main messages (user, assistant), show full format
    const textLines = wrapText(message.text, maxWidth - 4);

    return (
      <Box key={isPending ? 'pending' : message.id} flexDirection="column" marginY={1}>
        {/* Message header */}
        <Box justifyContent="space-between">
          <Text color={color} bold>
            {prefix}
          </Text>
          <Text color="gray" dimColor>
            {timestamp}
            {message.metadata?.target && (
              <Text> • {message.metadata.target.type}:{message.metadata.target.id}</Text>
            )}
            {isPending && (
              <Text color="yellow"> • streaming...</Text>
            )}
          </Text>
        </Box>

        {/* Message content */}
        <Box flexDirection="column" marginLeft={2} marginTop={1}>
          {textLines.map((line, index) => {
            // Simple markdown-like formatting
            let formattedLine = line;
            const isBold = line.startsWith('**') && line.endsWith('**');
            const isListItem = line.trim().startsWith('- ') || line.trim().startsWith('• ');
            const isHeader = line.startsWith('##') || line.startsWith('###');
            
            return (
              <Text 
                key={index} 
                color={isPending ? 'gray' : 'white'}
                bold={isBold}
                dimColor={isListItem}
              >
                {formattedLine}
              </Text>
            );
          })}
          {isPending && message.text && (
            <Text color="yellow">▊</Text> // Cursor for streaming
          )}
        </Box>
      </Box>
    );
  };

  // Show recent messages that fit in the available height
  const allMessages = [...history];
  if (pendingMessage) {
    allMessages.push(pendingMessage);
  }

  // Calculate how many messages we can show
  const visibleMessages = allMessages.slice(-10); // Show last 10 messages

  return (
    <Box flexDirection="column" height={maxHeight} marginY={1}>
      {visibleMessages.length === 0 ? (
        <Box justifyContent="center" alignItems="center" height="100%">
          <Text color="gray">
            Welcome! Start a conversation by typing a message below.
          </Text>
        </Box>
      ) : (
        <Box flexDirection="column">
          {visibleMessages.map((message, index) => {
            const isPending = Boolean(pendingMessage && message === pendingMessage);
            return renderMessage(message, isPending);
          })}
        </Box>
      )}
    </Box>
  );
};