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
import { GeminiStyleInput } from './components/GeminiStyleInput.js';
import { Footer } from './components/Footer.js';
import { ChatDisplay } from './components/ChatDisplay.js';
import { TargetTypeDialog } from './components/TargetTypeDialog.js';
import { TargetSelectionDialog } from './components/TargetSelectionDialog.js';
import { SessionSelectionDialog } from './components/SessionSelectionDialog.js';
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
  const [selectedTarget, setSelectedTarget] = useState<{ type: 'agent' | 'team' | 'workflow'; id: string; name: string } | null>(null);
  const [availableTargets, setAvailableTargets] = useState<{
    agents: any[];
    teams: any[];
    workflows: any[];
  }>({ agents: [], teams: [], workflows: [] });
  
  // UI flow state
  const [uiState, setUiState] = useState<'selecting_type' | 'selecting_target' | 'selecting_session' | 'chatting'>('selecting_type');
  const [selectedTargetType, setSelectedTargetType] = useState<'agent' | 'team' | 'workflow' | null>(null);

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
        
        if (appConfig.cliDebug) {
          console.log(`Loaded ${agentsResponse.data?.length || 0} agents, ${teamsResponse.data?.length || 0} teams, ${workflowsResponse.data?.length || 0} workflows`);
        }
        
        // Start with target type selection
        setUiState('selecting_type');

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
  }, []); // Remove addMessage dependency to prevent re-initialization

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

  const isGlobalInputActive = streamingState === StreamingState.Idle && connectionStatus === 'connected' && uiState === 'chatting';
  
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
    } else if (key.escape) {
      // Cancel current run/streaming - only when not actively typing in input
      if (streamingState !== StreamingState.Idle) {
        cancelStream();
      }
    }
  }, {
    isActive: !isGlobalInputActive
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

  // Interactive flow handlers
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
      // Start a new session
      setUiState('chatting');
    }
    // TODO: Handle existing session loading
  }, []);

  const handleBackToTargetType = useCallback(() => {
    setSelectedTargetType(null);
    setUiState('selecting_type');
  }, []);

  const handleBackToTargetSelection = useCallback(() => {
    setSelectedTarget(null);
    setUiState('selecting_target');
  }, []);

  const isInputActive = isGlobalInputActive;
  const widthFraction = 0.9;
  const inputWidth = Math.max(20, Math.floor(terminalWidth * widthFraction) - 3);

  // Show connection error
  if (connectionStatus === 'error') {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <Box
          borderStyle="round"
          borderColor="red"
          paddingX={1}
          marginY={1}
        >
          <Text color="red">
            Failed to connect to API at {appConfig.apiBaseUrl}
          </Text>
          <Text>Make sure the multi-agent server is running and try again.</Text>
        </Box>
        <Footer
          debugMode={appConfig.cliDebug}
          debugMessage={debugMessage}
          sessionId={currentSessionId}
          apiUrl={appConfig.apiBaseUrl}
        />
      </Box>
    );
  }

  // Show loading while connecting
  if (connectionStatus === 'connecting') {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <Text>🧞 Connecting to {appConfig.apiBaseUrl}...</Text>
        <Footer
          debugMode={appConfig.cliDebug}
          debugMessage={debugMessage}
          sessionId={currentSessionId}
          apiUrl={appConfig.apiBaseUrl}
        />
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
        <Footer
          debugMode={appConfig.cliDebug}
          debugMessage={debugMessage}
          sessionId={currentSessionId}
          apiUrl={appConfig.apiBaseUrl}
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
        <Footer
          debugMode={appConfig.cliDebug}
          debugMessage={debugMessage}
          sessionId={currentSessionId}
          apiUrl={appConfig.apiBaseUrl}
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
        <Footer
          debugMode={appConfig.cliDebug}
          debugMessage={debugMessage}
          sessionId={currentSessionId}
          apiUrl={appConfig.apiBaseUrl}
        />
      </Box>
    );
  }

  // Main chat interface
  return (
    <Box flexDirection="column" marginBottom={1} width="90%">
      <Header
        terminalWidth={terminalWidth}
        version={version}
        connectionStatus={connectionStatus}
        selectedTarget={selectedTarget}
        availableTargets={availableTargets}
        onTargetChange={() => setUiState('selecting_type')}
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
            <Text>• Esc: Cancel current run/streaming</Text>
            <Text>• Click target name to change selection</Text>
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

        {isInputActive && uiState === 'chatting' && (
          <GeminiStyleInput
            onSubmit={handleSubmit}
            disabled={!selectedTarget}
            placeholder={
              selectedTarget
                ? `Message ${selectedTarget.name}...`
                : 'No target selected'
            }
            focus={true}
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