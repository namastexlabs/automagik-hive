import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { HistoryItem, SessionData } from '../types.js';
import { appConfig } from '../../config/settings.js';
import { resolve } from 'path';
import { writeFile, readFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';

interface SessionContextType {
  history: HistoryItem[];
  currentSessionId: string;
  addMessage: (message: Omit<HistoryItem, 'id'>) => void;
  clearHistory: () => void;
  saveSession: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  createNewSession: () => void;
  listSessions: () => Promise<string[]>;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

interface SessionProviderProps {
  children: React.ReactNode;
}

export const SessionProvider: React.FC<SessionProviderProps> = ({ children }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [nextMessageId, setNextMessageId] = useState<number>(1);

  // Initialize session
  useEffect(() => {
    const initSession = async () => {
      const sessionId = generateSessionId();
      setCurrentSessionId(sessionId);
      
      // Ensure session directory exists
      try {
        const sessionDir = getSessionDir();
        if (!existsSync(sessionDir)) {
          await mkdir(sessionDir, { recursive: true });
        }
      } catch (error) {
        console.error('Failed to create session directory:', error);
      }
    };

    initSession();
  }, []);

  const generateSessionId = useCallback((): string => {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  const getSessionDir = useCallback((): string => {
    const sessionDir = appConfig.sessionDir.replace('~', process.env.HOME || '');
    return resolve(sessionDir);
  }, []);

  const getSessionFilePath = useCallback((sessionId: string): string => {
    return resolve(getSessionDir(), `${sessionId}.json`);
  }, [getSessionDir]);

  const addMessage = useCallback((message: Omit<HistoryItem, 'id'>) => {
    const newMessage: HistoryItem = {
      ...message,
      id: nextMessageId,
    };
    
    setHistory(prev => [...prev, newMessage]);
    setNextMessageId(prev => prev + 1);

    // Auto-save if enabled
    if (appConfig.sessionAutoSave) {
      setTimeout(() => saveSessionData(), 100); // Debounce saves
    }
  }, [nextMessageId]);

  const clearHistory = useCallback(() => {
    setHistory([]);
    setNextMessageId(1);
  }, []);

  const saveSessionData = useCallback(async (): Promise<void> => {
    if (!currentSessionId || history.length === 0) {
      return;
    }

    const sessionData: SessionData = {
      id: currentSessionId,
      messages: history,
      createdAt: history[0]?.timestamp || Date.now(),
      updatedAt: Date.now(),
      metadata: {
        totalMessages: history.length,
        lastTarget: history[history.length - 1]?.metadata?.target,
      },
    };

    try {
      const filePath = getSessionFilePath(currentSessionId);
      await writeFile(filePath, JSON.stringify(sessionData, null, 2), 'utf8');
      
      if (appConfig.cliDebug) {
        console.log(`Session saved: ${filePath}`);
      }
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  }, [currentSessionId, history, getSessionFilePath]);

  const loadSessionData = useCallback(async (sessionId: string): Promise<void> => {
    try {
      const filePath = getSessionFilePath(sessionId);
      const data = await readFile(filePath, 'utf8');
      const sessionData: SessionData = JSON.parse(data);
      
      setHistory(sessionData.messages);
      setCurrentSessionId(sessionId);
      setNextMessageId(Math.max(...sessionData.messages.map(m => m.id), 0) + 1);
      
      if (appConfig.cliDebug) {
        console.log(`Session loaded: ${filePath}`);
      }
    } catch (error) {
      console.error('Failed to load session:', error);
      throw error;
    }
  }, [getSessionFilePath]);

  const createNewSession = useCallback(() => {
    const newSessionId = generateSessionId();
    setCurrentSessionId(newSessionId);
    setHistory([]);
    setNextMessageId(1);
  }, [generateSessionId]);

  const listSessions = useCallback(async (): Promise<string[]> => {
    try {
      const { readdir } = await import('fs/promises');
      const sessionDir = getSessionDir();
      
      if (!existsSync(sessionDir)) {
        return [];
      }
      
      const files = await readdir(sessionDir);
      return files
        .filter(file => file.endsWith('.json'))
        .map(file => file.replace('.json', ''))
        .sort((a, b) => b.localeCompare(a)); // Most recent first
    } catch (error) {
      console.error('Failed to list sessions:', error);
      return [];
    }
  }, [getSessionDir]);

  const contextValue: SessionContextType = {
    history,
    currentSessionId,
    addMessage,
    clearHistory,
    saveSession: saveSessionData,
    loadSession: loadSessionData,
    createNewSession,
    listSessions,
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};