/**
 * Gemini-style App that uses the visual structure from gemini-cli
 * but connects to genie's backend (agents, teams, workflows)
 */

import { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import {
  Box,
  Static,
  Text,
  useStdin,
  useStdout,
  useInput,
  type Key as InkKeyType,
} from 'ink';
import { StreamingState, type HistoryItem, MessageType } from './types.js';
import { useTerminalSize } from './hooks/useTerminalSize.js';
import { useLocalAPIStream } from './hooks/useLocalAPIStream.js';
import { useLoadingIndicator } from './hooks/useLoadingIndicator.js';
import { Colors } from './colors.js';
import { Header } from './components/Header.js';
import { SessionProvider, useSession } from './contexts/SessionContext.js';
import { StreamingProvider } from './contexts/StreamingContext.js';
import { appConfig } from '../config/settings.js';
import { localAPIClient } from '../config/localClient.js';
import { useTextBuffer } from './components/shared/text-buffer.js';

// Simplified components that will work with our backend
import { TargetTypeDialog } from './components/TargetTypeDialog.js';
import { TargetSelectionDialog } from './components/TargetSelectionDialog.js';
import { SessionSelectionDialog } from './components/SessionSelectionDialog.js';
import { GeminiInputPrompt } from './components/GeminiInputPrompt.js';

const CTRL_EXIT_PROMPT_DURATION_MS = 1000;

interface GeminiAppProps {
  version: string;
}

export const GeminiAppWrapper = (props: GeminiAppProps) => (
  <SessionProvider>
    <StreamingProvider>
      <GeminiApp {...props} />
    </StreamingProvider>
  </SessionProvider>
);

const GeminiApp = ({ version }: GeminiAppProps) => {
  const { stdout } = useStdout();
  const { stdin, setRawMode } = useStdin();
  const { rows: terminalHeight, columns: terminalWidth } = useTerminalSize();
  
  // Session and history management
  const {
    history,
    addMessage,
    clearHistory,
    currentSessionId,
  } = useSession();

  // UI state for genie's flow
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [selectedTarget, setSelectedTarget] = useState<{ type: 'agent' | 'team' | 'workflow'; id: string; name: string } | null>(null);
  const [availableTargets, setAvailableTargets] = useState<{
    agents: any[];
    teams: any[];
    workflows: any[];
  }>({ agents: [], teams: [], workflows: [] });
  
  const [uiState, setUiState] = useState<'selecting_type' | 'selecting_target' | 'selecting_session' | 'chatting'>('selecting_type');
  const [selectedTargetType, setSelectedTargetType] = useState<'agent' | 'team' | 'workflow' | null>(null);

  // Gemini-style state
  const [debugMessage, setDebugMessage] = useState<string>('');
  const [ctrlCPressedOnce, setCtrlCPressedOnce] = useState(false);
  const [ctrlDPressedOnce, setCtrlDPressedOnce] = useState(false);
  const ctrlCTimerRef = useRef<NodeJS.Timeout | null>(null);
  const ctrlDTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Local API streaming
  const {
    streamingState,
    submitQuery,
    cancelStream,
    initError,
    pendingMessage,
  } = useLocalAPIStream(
    addMessage,
    selectedTarget,
    currentSessionId,
    setDebugMessage
  );

  const { elapsedTime, currentLoadingPhrase } = useLoadingIndicator(streamingState);

  // Text buffer for gemini-style input
  const widthFraction = 0.9;
  const inputWidth = Math.max(20, Math.floor(terminalWidth * widthFraction) - 3);
  
  const buffer = useTextBuffer({
    initialText: '',
    viewport: { height: 10, width: inputWidth },
    stdin,
    setRawMode,
    isValidPath: () => false, // Simplified for now
    shellModeActive: false,
  });

  // Initialize API connection
  useEffect(() => {
    const initializeAPI = async () => {
      try {
        // Add a small delay to ensure banner is visible
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const healthResponse = await localAPIClient.healthCheck();
        if (healthResponse.error) {
          throw new Error(healthResponse.error);
        }

        const [agentsResponse, teamsResponse, workflowsResponse] = await Promise.all([
          localAPIClient.listAgents(),
          localAPIClient.listTeams(),
          localAPIClient.listWorkflows(),
        ]);

        setAvailableTargets({
          agents: agentsResponse.data || [],
          teams: teamsResponse.data || [],
          workflows: workflowsResponse.data || [],
        });

        setConnectionStatus('connected');
        
        // Auto-select first agent for direct gemini-style interface
        if (agentsResponse.data && agentsResponse.data.length > 0) {
          const firstAgent = agentsResponse.data[0];
          setSelectedTarget({
            type: 'agent',
            id: firstAgent.agent_id,
            name: firstAgent.name
          });
          setUiState('chatting');
        } else {
          setUiState('selecting_type');
        }

      } catch (error) {
        setConnectionStatus('error');
        addMessage({
          type: MessageType.ERROR,
          text: `Failed to connect to API: ${error instanceof Error ? error.message : 'Unknown error'}`,
          timestamp: Date.now(),
        });
      }
    };

    initializeAPI();
  }, [addMessage]);

  const handleExit = useCallback(
    (
      pressedOnce: boolean,
      setPressedOnce: (value: boolean) => void,
      timerRef: React.MutableRefObject<NodeJS.Timeout | null>,
    ) => {
      if (pressedOnce) {
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
        process.exit(0);
      } else {
        setPressedOnce(true);
        timerRef.current = setTimeout(() => {
          setPressedOnce(false);
          timerRef.current = null;
        }, CTRL_EXIT_PROMPT_DURATION_MS);
      }
    },
    [],
  );

  const isInputActive = streamingState === StreamingState.Idle && connectionStatus === 'connected' && uiState === 'chatting';

  useInput((input: string, key: InkKeyType) => {
    if (key.ctrl && (input === 'c' || input === 'C')) {
      handleExit(ctrlCPressedOnce, setCtrlCPressedOnce, ctrlCTimerRef);
    } else if (key.ctrl && (input === 'd' || input === 'D')) {
      handleExit(ctrlDPressedOnce, setCtrlDPressedOnce, ctrlDTimerRef);
    } else if (key.ctrl && input === 'l') {
      clearHistory();
      stdout.write('\\x1B[2J\\x1B[3J\\x1B[H'); // Clear screen
    } else if (key.escape) {
      if (streamingState !== StreamingState.Idle) {
        cancelStream();
      }
    }
  }, {
    isActive: !isInputActive
  });

  const handleFinalSubmit = useCallback(
    (submittedValue: string) => {
      const trimmedValue = submittedValue.trim();
      if (trimmedValue.length > 0 && selectedTarget) {
        submitQuery(trimmedValue);
      }
    },
    [submitQuery, selectedTarget],
  );

  // Flow handlers
  const handleTargetTypeSelect = useCallback((targetType: 'agent' | 'team' | 'workflow') => {
    setSelectedTargetType(targetType);
    setUiState('selecting_target');
  }, []);

  const handleTargetSelect = useCallback((target: { type: 'agent' | 'team' | 'workflow'; id: string; name: string }) => {
    setSelectedTarget(target);
    setUiState('selecting_session');
  }, []);

  const handleSessionSelect = useCallback((sessionAction: 'new' | 'existing') => {
    if (sessionAction === 'new') {
      setUiState('chatting');
    }
  }, []);

  const handleBackToTargetType = useCallback(() => {
    setSelectedTargetType(null);
    setUiState('selecting_type');
  }, []);

  const handleBackToTargetSelection = useCallback(() => {
    setSelectedTarget(null);
    setUiState('selecting_target');
  }, []);

  const handleClearScreen = useCallback(() => {
    clearHistory();
    stdout.write('\\x1B[2J\\x1B[3J\\x1B[H');
  }, [clearHistory, stdout]);

  const mainAreaWidth = Math.floor(terminalWidth * 0.9);

  // Show connection error
  if (connectionStatus === 'error') {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <Header
          terminalWidth={terminalWidth}
          version={version}
          nightly={false}
        />
        <Box marginTop={2}>
          <Box borderStyle="round" borderColor={Colors.AccentRed} paddingX={1} marginY={1}>
            <Text color={Colors.AccentRed}>
              Failed to connect to API at {appConfig.apiBaseUrl}
            </Text>
          </Box>
        </Box>
      </Box>
    );
  }

  // Show loading while connecting
  if (connectionStatus === 'connecting') {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <Header
          terminalWidth={terminalWidth}
          version={version}
          nightly={false}
        />
        <Box marginTop={2}>
          <Text>🔗 Connecting to {appConfig.apiBaseUrl}...</Text>
        </Box>
      </Box>
    );
  }

  // Interactive setup flow
  if (uiState === 'selecting_type') {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <TargetTypeDialog
          onSelect={handleTargetTypeSelect}
          availableTargets={availableTargets}
        />
      </Box>
    );
  }

  if (uiState === 'selecting_target' && selectedTargetType) {
    const targets = selectedTargetType === 'agent' 
      ? availableTargets.agents 
      : selectedTargetType === 'team' 
      ? availableTargets.teams 
      : availableTargets.workflows;

    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <TargetSelectionDialog
          targetType={selectedTargetType}
          targets={targets}
          onSelect={handleTargetSelect}
          onBack={handleBackToTargetType}
        />
      </Box>
    );
  }

  if (uiState === 'selecting_session' && selectedTarget) {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <SessionSelectionDialog
          selectedTarget={selectedTarget}
          onSelect={handleSessionSelect}
          onBack={handleBackToTargetSelection}
        />
      </Box>
    );
  }

  // Main chat interface with gemini styling
  return (
    <Box flexDirection="column" marginBottom={1} width="90%">
      {/* Gemini-style header */}
      <Box 
        borderStyle="round" 
        borderColor={Colors.AccentPurple} 
        paddingX={1} 
        marginBottom={1}
        justifyContent="space-between"
      >
        <Box>
          <Text bold color="cyan">🎯 Genie Local CLI</Text>
          <Text color="gray"> v{version}</Text>
        </Box>
        <Text color={Colors.AccentCyan}>● Connected</Text>
      </Box>

      {/* Target info banner with gemini styling */}
      <Box 
        borderStyle="round" 
        borderColor="magenta" 
        paddingX={1} 
        marginBottom={1}
      >
        <Text color="magenta">
          💬 Chatting with: {selectedTarget?.name}
        </Text>
        <Text color="gray"> ({selectedTarget?.type})</Text>
      </Box>

      {/* Chat history */}
      <Static
        items={history.map((h, index) => (
          <Box key={`history-${h.id}-${index}`} marginBottom={1}>
            <Text color={h.type === MessageType.USER ? Colors.AccentPurple : "white"}>
              {h.type === MessageType.USER ? '> ' : '< '}{h.text}
            </Text>
          </Box>
        ))}
      >
        {(item) => item}
      </Static>

      {/* Pending message */}
      {pendingMessage && (
        <Box marginBottom={1}>
          <Text color="white">
            {'< '}{pendingMessage.text}
          </Text>
        </Box>
      )}

      {/* Loading indicator */}
      {streamingState !== StreamingState.Idle && (
        <Box marginBottom={1}>
          <Text color="yellow">
            {currentLoadingPhrase} ({elapsedTime > 0 ? `${Math.floor(elapsedTime / 1000)}s` : ''})
          </Text>
        </Box>
      )}

      {/* Exit prompts */}
      {ctrlCPressedOnce ? (
        <Text color="yellow">Press Ctrl+C again to exit.</Text>
      ) : ctrlDPressedOnce ? (
        <Text color="yellow">Press Ctrl+D again to exit.</Text>
      ) : null}

      {/* Input prompt with gemini styling */}
      {isInputActive && (
        <GeminiInputPrompt
          buffer={buffer}
          onSubmit={handleFinalSubmit}
          onClearScreen={handleClearScreen}
          placeholder="  Type your message..."
          focus={true}
          inputWidth={inputWidth}
          shellModeActive={false}
          isActive={isInputActive}
        />
      )}

      {/* Footer */}
      <Box 
        borderStyle="round" 
        borderColor="gray" 
        paddingX={1} 
        marginTop={1}
        justifyContent="space-between"
      >
        <Box>
          <Text color="gray">
            Session: {currentSessionId.slice(-8)}
          </Text>
        </Box>
        <Box>
          <Text color="gray">
            API: {appConfig.apiBaseUrl}
          </Text>
        </Box>
      </Box>

      {/* Debug */}
      {appConfig.cliDebug && debugMessage && (
        <Box marginTop={1} borderStyle="round" borderColor="yellow" paddingX={1}>
          <Text color="yellow">Debug: {debugMessage}</Text>
        </Box>
      )}
    </Box>
  );
};