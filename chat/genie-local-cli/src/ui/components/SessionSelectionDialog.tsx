import React, { useState, useEffect } from 'react';
import { Box, Text, useInput } from 'ink';
import { RadioButtonSelect } from './RadioButtonSelect.js';
import { Colors } from '../colors.js';
import { useSession } from '../contexts/SessionContext.js';
import { SessionData } from '../types.js';

interface SessionSelectionDialogProps {
  selectedTarget: { type: 'agent' | 'team' | 'workflow'; id: string; name: string };
  onSelect: (sessionAction: 'new' | 'existing', sessionId?: string) => void;
  onBack: () => void;
}

export function SessionSelectionDialog({
  selectedTarget,
  onSelect,
  onBack,
}: SessionSelectionDialogProps): React.JSX.Element {
  const { listSessions, listBackendSessions } = useSession();
  const [existingSessions, setExistingSessions] = useState<SessionData[]>([]);
  const [backendSessions, setBackendSessions] = useState<any[]>([]);
  const [showSessionList, setShowSessionList] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadSessions = async () => {
      setLoading(true);
      try {
        const [localSessions, remoteSessions] = await Promise.all([
          listSessions(selectedTarget),
          listBackendSessions(selectedTarget)
        ]);
        
        setExistingSessions(localSessions);
        setBackendSessions(remoteSessions);
      } catch (error) {
        console.error('Failed to load sessions:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSessions();
  }, [selectedTarget, listSessions, listBackendSessions]);

  const hasExistingSessions = existingSessions.length > 0 || backendSessions.length > 0;

  const items = [
    {
      label: 'Start new conversation',
      value: 'new' as const,
    },
    {
      label: hasExistingSessions ? 'Continue existing session' : 'Continue existing session (no sessions found)',
      value: 'existing' as const,
      disabled: !hasExistingSessions,
    },
  ];

  const handleSelect = (sessionAction: 'new' | 'existing') => {
    if (sessionAction === 'existing' && hasExistingSessions) {
      setShowSessionList(true);
    } else {
      onSelect(sessionAction);
    }
  };

  const handleSessionSelect = (sessionId: string) => {
    onSelect('existing', sessionId);
  };

  useInput((input, key) => {
    if (key.escape) {
      if (showSessionList) {
        setShowSessionList(false);
      } else {
        onBack();
      }
    }
  });

  if (showSessionList) {
    const formatSessionTime = (timestamp: number) => {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else if (diffDays === 1) {
        return 'Yesterday';
      } else if (diffDays < 7) {
        return `${diffDays} days ago`;
      } else {
        return date.toLocaleDateString();
      }
    };

    const sessionItems = [
      ...existingSessions.map(session => ({
        label: `${formatSessionTime(session.updatedAt)} (${session.metadata?.totalMessages || 0} messages)`,
        value: session.id,
      })),
      ...backendSessions.map(session => ({
        label: `${session.name || session.id} (Backend)`,
        value: session.id,
      })),
    ];

    return (
      <Box
        borderStyle="round"
        borderColor={Colors.AccentPurple}
        flexDirection="column"
        padding={1}
        width="100%"
      >
        <Text bold color={Colors.AccentPurple}>Select Session</Text>
        <Box marginTop={1}>
          <Text color={Colors.Foreground}>Choose a session to continue:</Text>
        </Box>
        <Box marginTop={1}>
          <RadioButtonSelect
            items={sessionItems}
            initialIndex={0}
            onSelect={handleSessionSelect}
            isFocused={true}
          />
        </Box>
        <Box marginTop={1}>
          <Text color={Colors.Gray}>(Use ↑/↓ arrows and Enter to select, Esc to go back)</Text>
        </Box>
      </Box>
    );
  }

  return (
    <Box
      borderStyle="round"
      borderColor={Colors.AccentPurple}
      flexDirection="column"
      padding={1}
      width="100%"
    >
      <Text bold color={Colors.AccentPurple}>Session Options</Text>
      <Box marginTop={1}>
        <Text color={Colors.Foreground}>Ready to chat with: <Text color={Colors.AccentCyan}>{selectedTarget.name}</Text></Text>
      </Box>
      <Box marginTop={1}>
        <Text color={Colors.Foreground}>How would you like to proceed?</Text>
      </Box>
      {loading && (
        <Box marginTop={1}>
          <Text color={Colors.Gray}>Loading sessions...</Text>
        </Box>
      )}
      {!loading && (
        <Box marginTop={1}>
          <RadioButtonSelect
            items={items}
            initialIndex={0}
            onSelect={handleSelect}
            isFocused={true}
          />
        </Box>
      )}
      <Box marginTop={1}>
        <Text color={Colors.Gray}>(Use ↑/↓ arrows and Enter to select, Esc to go back)</Text>
      </Box>
      {hasExistingSessions && (
        <Box marginTop={1}>
          <Text color={Colors.AccentGreen}>Found {existingSessions.length} local sessions and {backendSessions.length} backend sessions</Text>
        </Box>
      )}
    </Box>
  );
}