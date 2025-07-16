/**
 * Exact copy of gemini-cli App.tsx but adapted for Genie backend
 */

import { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import {
  Box,
  DOMElement,
  measureElement,
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
import { Header } from './components/Header.js';
import { LoadingIndicator } from './components/LoadingIndicator.js';
import { InputPrompt } from './components/InputPrompt.js';
import { Footer } from './components/Footer.js';
import { Colors } from './colors.js';
import { HistoryItemDisplay } from './components/HistoryItemDisplay.js';
import { TargetSelectionDialog } from './components/TargetSelectionDialog.js';
import { TargetTypeDialog } from './components/TargetTypeDialog.js';
import { SessionSelectionDialog } from './components/SessionSelectionDialog.js';
import { useTextBuffer } from './components/shared/text-buffer.js';
import { SessionProvider, useSession } from './contexts/SessionContext.js';
import { StreamingProvider } from './contexts/StreamingContext.js';
import { appConfig } from '../config/settings.js';
import { localAPIClient } from '../config/localClient.js';
import { detectAPIServer, generateStartupGuide } from '../utils/serverDetection.js';
import ansiEscapes from 'ansi-escapes';

const CTRL_EXIT_PROMPT_DURATION_MS = 1000;

interface AppProps {
  version: string;
}

export const AppWrapper = (props: AppProps) => {
  return (
    <SessionProvider>
      <StreamingProvider>
        <App {...props} />
      </StreamingProvider>
    </SessionProvider>
  );
};

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
    createNewSession,
    loadSession,
    setCurrentTarget,
    listSessions,
    listBackendSessions,
  } = useSession();

  // UI state
  const [staticNeedsRefresh, setStaticNeedsRefresh] = useState(false);
  const [staticKey, setStaticKey] = useState(0);
  const [debugMessage, setDebugMessage] = useState<string>('');
  const [ctrlCPressedOnce, setCtrlCPressedOnce] = useState(false);
  const [ctrlDPressedOnce, setCtrlDPressedOnce] = useState(false);
  const ctrlCTimerRef = useRef<NodeJS.Timeout | null>(null);
  const ctrlDTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [constrainHeight, setConstrainHeight] = useState<boolean>(true);
  const [footerHeight, setFooterHeight] = useState<number>(0);
  const [shellModeActive, setShellModeActive] = useState<boolean>(false);
  
  // Target selection state
  const [uiState, setUiState] = useState<'selecting_type' | 'selecting_target' | 'selecting_session' | 'chatting'>('selecting_type');
  const [selectedTargetType, setSelectedTargetType] = useState<'agent' | 'team' | 'workflow' | null>(null);
  
  // API state
  const [showStartupBanner, setShowStartupBanner] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [selectedTarget, setSelectedTarget] = useState<{ type: 'agent' | 'team' | 'workflow'; id: string; name: string } | null>(null);
  const [availableTargets, setAvailableTargets] = useState<{
    agents: any[];
    teams: any[];
    workflows: any[];
  }>({ agents: [], teams: [], workflows: [] });

  const refreshStatic = useCallback(() => {
    stdout.write(ansiEscapes.clearTerminal);
    setStaticKey((prev) => prev + 1);
  }, [setStaticKey, stdout]);

  // Target selection handlers
  const handleTargetTypeSelect = useCallback((targetType: 'agent' | 'team' | 'workflow') => {
    setSelectedTargetType(targetType);
    setUiState('selecting_target');
  }, []);

  const handleTargetSelect = useCallback((target: { type: 'agent' | 'team' | 'workflow'; id: string; name: string }) => {
    setSelectedTarget(target);
    setCurrentTarget(target);
    setUiState('selecting_session');
  }, [setCurrentTarget]);

  const handleBackToTargetSelection = useCallback(() => {
    setUiState('selecting_type');
    setSelectedTargetType(null);
  }, []);

  const handleBackToTargetSelect = useCallback(() => {
    setUiState('selecting_target');
  }, []);

  const handleSessionSelect = useCallback(async (sessionAction: 'new' | 'existing', sessionId?: string) => {
    if (sessionAction === 'new') {
      createNewSession(selectedTarget || undefined);
    } else if (sessionAction === 'existing' && sessionId) {
      try {
        await loadSession(sessionId);
      } catch (error) {
        console.error('Failed to load session:', error);
        addMessage({
          type: MessageType.ERROR,
          text: `Failed to load session: ${error instanceof Error ? error.message : 'Unknown error'}`,
          timestamp: Date.now(),
        });
      }
    }
    setUiState('chatting');
  }, [selectedTarget, createNewSession, loadSession, addMessage]);

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

  // Text buffer setup
  const widthFraction = 0.9;
  const inputWidth = Math.max(20, Math.floor(terminalWidth * widthFraction) - 3);
  const suggestionsWidth = Math.max(60, Math.floor(terminalWidth * 0.8));

  const buffer = useTextBuffer({
    initialText: '',
    viewport: { height: 10, width: inputWidth },
    stdin,
    setRawMode,
    isValidPath: () => false,
    shellModeActive: false,
  });

  // Show startup banner for 2 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowStartupBanner(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

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
        
        // Auto-select first agent for direct interface
        if (agentsResponse.data && agentsResponse.data.length > 0) {
          const firstAgent = agentsResponse.data[0];
          setSelectedTarget({
            type: 'agent',
            id: firstAgent.agent_id,
            name: firstAgent.name
          });
        }

      } catch (error) {
        setConnectionStatus('error');
        
        // Use graceful server detection
        const serverStatus = await detectAPIServer(appConfig.apiBaseUrl);
        const startupGuide = generateStartupGuide(serverStatus);
        
        addMessage({
          type: MessageType.ERROR,
          text: startupGuide,
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

  const isInputActive = streamingState === StreamingState.Idle && !initError && connectionStatus === 'connected' && uiState === 'chatting';

  useInput((input: string, key: InkKeyType) => {
    let enteringConstrainHeightMode = false;
    if (!constrainHeight) {
      enteringConstrainHeightMode = true;
      setConstrainHeight(true);
    }

    if (key.ctrl && (input === 'c' || input === 'C')) {
      handleExit(ctrlCPressedOnce, setCtrlCPressedOnce, ctrlCTimerRef);
    } else if (key.ctrl && (input === 'd' || input === 'D')) {
      if (buffer.text.length > 0) {
        return;
      }
      handleExit(ctrlDPressedOnce, setCtrlDPressedOnce, ctrlDTimerRef);
    } else if (key.ctrl && input === 's' && !enteringConstrainHeightMode) {
      setConstrainHeight(false);
    }
  });

  const handleFinalSubmit = useCallback(
    async (submittedValue: string) => {
      const trimmedValue = submittedValue.trim();
      
      // Handle slash commands
      if (trimmedValue.startsWith('/')) {
        const command = trimmedValue.toLowerCase();
        
        if (command === '/sessions') {
          try {
            const sessions = await listSessions();
            const backendSessions = selectedTarget ? await listBackendSessions(selectedTarget) : [];
            
            let sessionList = '📚 **Available Sessions**\n\n';
            
            if (sessions.length > 0) {
              sessionList += '**Local Sessions:**\n';
              sessions.forEach((session, index) => {
                const date = new Date(session.updatedAt).toLocaleDateString();
                const time = new Date(session.updatedAt).toLocaleTimeString();
                const messageCount = session.metadata?.totalMessages || 0;
                const target = session.metadata?.lastTarget;
                const targetDisplay = target ? `${target.type}:${target.name || target.id}` : 'Unknown';
                
                sessionList += `${index + 1}. ${session.id}\n`;
                sessionList += `   📅 ${date} ${time} | 💬 ${messageCount} messages | 🎯 ${targetDisplay}\n\n`;
              });
            }
            
            if (backendSessions.length > 0) {
              sessionList += '**Backend Sessions:**\n';
              backendSessions.forEach((session, index) => {
                sessionList += `${index + 1}. ${session.id || session.name}\n`;
                sessionList += `   📍 Backend session\n\n`;
              });
            }
            
            if (sessions.length === 0 && backendSessions.length === 0) {
              sessionList += 'No sessions found.\n';
            }
            
            sessionList += '\n💡 **Tips:**\n';
            sessionList += '- Select a target (agent/team/workflow) to see available sessions\n';
            sessionList += '- Use session selection dialog to continue existing sessions\n';
            sessionList += '- Local sessions are stored in ~/.genie-cli/sessions/\n';
            
            addMessage({
              type: MessageType.INFO,
              text: sessionList,
              timestamp: Date.now(),
            });
          } catch (error) {
            addMessage({
              type: MessageType.ERROR,
              text: `Failed to list sessions: ${error instanceof Error ? error.message : 'Unknown error'}`,
              timestamp: Date.now(),
            });
          }
          return;
        }
        
        // Handle unknown commands
        addMessage({
          type: MessageType.ERROR,
          text: `Unknown command: ${trimmedValue}\n\nAvailable commands:\n- /sessions - List all available sessions`,
          timestamp: Date.now(),
        });
        return;
      }
      
      // Handle regular messages
      if (trimmedValue.length > 0 && selectedTarget) {
        submitQuery(trimmedValue);
      }
    },
    [submitQuery, selectedTarget, listSessions, listBackendSessions, addMessage],
  );

  const handleClearScreen = useCallback(() => {
    clearHistory();
    console.clear();
    refreshStatic();
  }, [clearHistory, refreshStatic]);

  const mainControlsRef = useRef<DOMElement>(null);

  useEffect(() => {
    if (mainControlsRef.current) {
      const fullFooterMeasurement = measureElement(mainControlsRef.current);
      setFooterHeight(fullFooterMeasurement.height);
    }
  }, [terminalHeight]);

  const staticExtraHeight = 3;
  const availableTerminalHeight = useMemo(
    () => terminalHeight - footerHeight - staticExtraHeight,
    [terminalHeight, footerHeight],
  );

  const mainAreaWidth = Math.floor(terminalWidth * 0.9);
  const staticAreaMaxItemHeight = Math.max(terminalHeight * 4, 100);

  // Show startup banner first
  if (showStartupBanner) {
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

  // Show connection error
  if (connectionStatus === 'error') {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <Static
          key={staticKey}
          items={[
            <Box flexDirection="column" key="header">
              <Header
                terminalWidth={terminalWidth}
                version={version}
                nightly={false}
              />
            </Box>,
          ]}
        >
          {() => null}
        </Static>
        <Box marginTop={2}>
          <Box
            borderStyle="round"
            borderColor={Colors.AccentRed}
            paddingX={1}
            marginY={1}
          >
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
        <Static
          key={staticKey}
          items={[
            <Box flexDirection="column" key="header">
              <Header
                terminalWidth={terminalWidth}
                version={version}
                nightly={false}
              />
            </Box>,
          ]}
        >
          {() => null}
        </Static>
        <Box marginTop={2}>
          <Text>🔗 Connecting to {appConfig.apiBaseUrl}...</Text>
        </Box>
      </Box>
    );
  }

  // Target selection UI
  if (uiState === 'selecting_type') {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <Static
          key={staticKey}
          items={[
            <Box flexDirection="column" key="header">
              <Header
                terminalWidth={terminalWidth}
                version={version}
                nightly={false}
              />
            </Box>,
          ]}
        >
          {() => null}
        </Static>
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
        <Static
          key={staticKey}
          items={[
            <Box flexDirection="column" key="header">
              <Header
                terminalWidth={terminalWidth}
                version={version}
                nightly={false}
              />
            </Box>,
          ]}
        >
          {() => null}
        </Static>
        <TargetSelectionDialog
          targetType={selectedTargetType}
          targets={targets}
          onSelect={handleTargetSelect}
          onBack={handleBackToTargetSelection}
        />
      </Box>
    );
  }

  if (uiState === 'selecting_session' && selectedTarget) {
    return (
      <Box flexDirection="column" marginBottom={1} width="90%">
        <Static
          key={staticKey}
          items={[
            <Box flexDirection="column" key="header">
              <Header
                terminalWidth={terminalWidth}
                version={version}
                nightly={false}
              />
            </Box>,
          ]}
        >
          {() => null}
        </Static>
        <SessionSelectionDialog
          selectedTarget={selectedTarget}
          onSelect={handleSessionSelect}
          onBack={handleBackToTargetSelect}
        />
      </Box>
    );
  }

  return (
    <Box flexDirection="column" marginBottom={1} width="90%">
      <Static
        key={staticKey}
        items={[
          <Box flexDirection="column" key="header">
            <Header
              terminalWidth={terminalWidth}
              version={version}
              nightly={false}
            />
          </Box>,
          ...history.map((h) => (
            <HistoryItemDisplay
              terminalWidth={mainAreaWidth}
              availableTerminalHeight={staticAreaMaxItemHeight}
              key={h.id}
              item={h}
              isPending={false}
            />
          )),
        ]}
      >
        {(item) => item}
      </Static>

      <Box flexDirection="column" ref={mainControlsRef}>
        <LoadingIndicator
          currentLoadingPhrase={currentLoadingPhrase}
          elapsedTime={elapsedTime}
          streamingState={streamingState}
        />

        {ctrlCPressedOnce ? (
          <Text color={Colors.AccentYellow}>Press Ctrl+C again to exit.</Text>
        ) : ctrlDPressedOnce ? (
          <Text color={Colors.AccentYellow}>Press Ctrl+D again to exit.</Text>
        ) : null}

        {initError && streamingState !== StreamingState.Responding && (
          <Box
            borderStyle="round"
            borderColor={Colors.AccentRed}
            paddingX={1}
            marginBottom={1}
          >
            <Text color={Colors.AccentRed}>
              Initialization Error: {initError}
            </Text>
          </Box>
        )}

        {isInputActive && (
          <InputPrompt
            buffer={buffer}
            onSubmit={handleFinalSubmit}
            userMessages={[]}
            onClearScreen={handleClearScreen}
            inputWidth={inputWidth}
            suggestionsWidth={suggestionsWidth}
            shellModeActive={shellModeActive}
            setShellModeActive={setShellModeActive}
          />
        )}

        <Footer
          selectedTarget={selectedTarget || undefined}
          sessionId={currentSessionId}
          apiUrl={appConfig.apiBaseUrl}
          debugMode={appConfig.cliDebug}
          debugMessage={debugMessage}
        />
      </Box>
    </Box>
  );
};

export default App;