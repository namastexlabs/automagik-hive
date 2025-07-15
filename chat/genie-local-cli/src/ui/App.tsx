import React, { useCallback, useEffect, useState, useRef } from 'react';
import {
  Box,
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
import { Header } from './components/Header.js';
import { LoadingIndicator } from './components/LoadingIndicator.js';
import { InputPrompt } from './components/InputPrompt.js';
import { Footer } from './components/Footer.js';
import { ChatDisplay } from './components/ChatDisplay.js';
import { SessionProvider, useSession } from './contexts/SessionContext.js';
import { StreamingProvider } from './contexts/StreamingContext.js';
import { appConfig } from '../config/settings.js';
import { localAPIClient } from '../config/localClient.js';

const CTRL_EXIT_PROMPT_DURATION_MS = 1000;

interface AppProps {
  version: string;
}

export const AppWrapper = (props: AppProps) => (
  <SessionProvider>
    <StreamingProvider>
      <App {...props} />
    </StreamingProvider>
  </SessionProvider>
);

const App = ({ version }: AppProps) => {
  const { stdout } = useStdout();
  const { stdin, setRawMode } = useStdin();
  const { rows: terminalHeight, columns: terminalWidth } = useTerminalSize();
  
  // Session and history management
  const {
    history,
    addMessage,
    clearHistory,
    currentSessionId,
    saveSession,
    loadSession,
  } = useSession();

  // UI state
  const [showHelp, setShowHelp] = useState<boolean>(false);
  const [debugMessage, setDebugMessage] = useState<string>('');
  const [ctrlCPressedOnce, setCtrlCPressedOnce] = useState(false);
  const [ctrlDPressedOnce, setCtrlDPressedOnce] = useState(false);
  const ctrlCTimerRef = useRef<NodeJS.Timeout | null>(null);
  const ctrlDTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // API state
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [selectedTarget, setSelectedTarget] = useState<{ type: 'agent' | 'team' | 'workflow'; id: string } | null>(null);
  const [availableTargets, setAvailableTargets] = useState<{
    agents: string[];
    teams: string[];
    workflows: string[];
  }>({ agents: [], teams: [], workflows: [] });

  // Local API streaming
  const {
    streamingState,
    submitQuery,
    initError,
    pendingMessage,
  } = useLocalAPIStream(
    addMessage,
    selectedTarget,
    currentSessionId,
    setDebugMessage
  );

  const { elapsedTime, currentLoadingPhrase } = useLoadingIndicator(streamingState);

  // Check API connection and load available targets
  useEffect(() => {
    const initializeAPI = async () => {
      try {
        // Health check
        const healthResponse = await localAPIClient.healthCheck();
        if (healthResponse.error) {
          throw new Error(healthResponse.error);
        }

        // Load available targets
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
        
        // Auto-select first available target
        if (agentsResponse.data && agentsResponse.data.length > 0) {
          setSelectedTarget({ type: 'agent', id: agentsResponse.data[0] });
        } else if (teamsResponse.data && teamsResponse.data.length > 0) {
          setSelectedTarget({ type: 'team', id: teamsResponse.data[0] });
        } else if (workflowsResponse.data && workflowsResponse.data.length > 0) {
          setSelectedTarget({ type: 'workflow', id: workflowsResponse.data[0] });
        }

      } catch (error) {
        console.error('Failed to connect to API:', error);
        setConnectionStatus('error');
        addMessage({
          type: MessageType.ERROR,
          text: `Failed to connect to API at ${appConfig.apiBaseUrl}: ${error instanceof Error ? error.message : 'Unknown error'}`,
          timestamp: Date.now(),
        });
      }
    };

    initializeAPI();
  }, [addMessage]);

  // Handle keyboard shortcuts
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

  useInput((input: string, key: InkKeyType) => {
    if (key.ctrl && (input === 'c' || input === 'C')) {
      handleExit(ctrlCPressedOnce, setCtrlCPressedOnce, ctrlCTimerRef);
    } else if (key.ctrl && (input === 'd' || input === 'D')) {
      handleExit(ctrlDPressedOnce, setCtrlDPressedOnce, ctrlDTimerRef);
    } else if (key.ctrl && input === 'h') {
      setShowHelp((prev) => !prev);
    } else if (key.ctrl && input === 'l') {
      clearHistory();
      stdout.write('\\x1B[2J\\x1B[3J\\x1B[H'); // Clear screen
    }
  });

  const handleSubmit = useCallback(
    (message: string) => {
      const trimmedMessage = message.trim();
      if (trimmedMessage.length > 0 && selectedTarget) {
        submitQuery(trimmedMessage);
      }
    },
    [submitQuery, selectedTarget],
  );

  const handleTargetChange = useCallback((newTarget: { type: 'agent' | 'team' | 'workflow'; id: string }) => {
    setSelectedTarget(newTarget);
  }, []);

  const isInputActive = streamingState === StreamingState.Idle && connectionStatus === 'connected';
  const widthFraction = 0.9;
  const inputWidth = Math.max(20, Math.floor(terminalWidth * widthFraction) - 3);

  return (
    <Box flexDirection="column" marginBottom={1} width="90%">
      <Header
        terminalWidth={terminalWidth}
        version={version}
        connectionStatus={connectionStatus}
        selectedTarget={selectedTarget}
        availableTargets={availableTargets}
        onTargetChange={handleTargetChange}
      />

      <ChatDisplay
        history={history}
        pendingMessage={pendingMessage}
        terminalWidth={terminalWidth}
        terminalHeight={terminalHeight}
      />

      {showHelp && (
        <Box 
          borderStyle="round" 
          borderColor="blue" 
          paddingX={1} 
          marginY={1}
        >
          <Box flexDirection="column">
            <Text bold>Genie Local CLI Help</Text>
            <Text>• Type messages to chat with the selected agent/team/workflow</Text>
            <Text>• Ctrl+H: Toggle this help</Text>
            <Text>• Ctrl+L: Clear screen</Text>
            <Text>• Ctrl+C or Ctrl+D (twice): Exit</Text>
            <Text>• Use the target selector to switch between agents, teams, and workflows</Text>
          </Box>
        </Box>
      )}

      <Box flexDirection="column">
        {ctrlCPressedOnce ? (
          <Text color="yellow">Press Ctrl+C again to exit.</Text>
        ) : ctrlDPressedOnce ? (
          <Text color="yellow">Press Ctrl+D again to exit.</Text>
        ) : null}

        <LoadingIndicator
          currentLoadingPhrase={currentLoadingPhrase}
          elapsedTime={elapsedTime}
          streamingState={streamingState}
        />

        {initError && (
          <Box
            borderStyle="round"
            borderColor="red"
            paddingX={1}
            marginBottom={1}
          >
            <Text color="red">
              Error: {initError}
            </Text>
          </Box>
        )}

        {isInputActive && (
          <InputPrompt
            onSubmit={handleSubmit}
            inputWidth={inputWidth}
            disabled={!selectedTarget}
            placeholder={
              selectedTarget
                ? `Message ${selectedTarget.type} ${selectedTarget.id}...`
                : 'No target selected'
            }
          />
        )}

        <Footer
          debugMode={appConfig.cliDebug}
          debugMessage={debugMessage}
          sessionId={currentSessionId}
          apiUrl={appConfig.apiBaseUrl}
        />
      </Box>
    </Box>
  );
};

export default App;