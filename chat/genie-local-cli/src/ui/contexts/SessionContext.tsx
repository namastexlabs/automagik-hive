import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { HistoryItem, SessionData, TargetInfo } from '../types.js';
import { appConfig } from '../../config/settings.js';
import { resolve } from 'path';
import { writeFile, readFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';

interface SessionContextType {
  history: HistoryItem[];
  currentSessionId: string;
  currentTarget: TargetInfo | null;
  addMessage: (message: Omit<HistoryItem, 'id'>) => void;
  clearHistory: () => void;
  saveSession: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  createNewSession: (target?: TargetInfo) => void;
  listSessions: (target?: TargetInfo) => Promise<SessionData[]>;
  listBackendSessions: (target: TargetInfo) => Promise<any[]>;
  deleteSession: (sessionId: string) => Promise<void>;
  getSessionMetadata: (sessionId: string) => Promise<SessionData | null>;
  setCurrentTarget: (target: TargetInfo | null) => void;
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
  const [currentTarget, setCurrentTarget] = useState<TargetInfo | null>(null);
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
      saveSessionData(); // No delay
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

  const createNewSession = useCallback((target?: TargetInfo) => {
    const newSessionId = generateSessionId();
    setCurrentSessionId(newSessionId);
    setHistory([]);
    setNextMessageId(1);
    if (target) {
      setCurrentTarget(target);
    }
  }, [generateSessionId]);

  const listSessions = useCallback(async (target?: TargetInfo): Promise<SessionData[]> => {
    try {
      const { readdir } = await import('fs/promises');
      const sessionDir = getSessionDir();
      
      if (!existsSync(sessionDir)) {
        return [];
      }
      
      const files = await readdir(sessionDir);
      const sessionFiles = files.filter(file => file.endsWith('.json'));
      
      const sessions: SessionData[] = [];
      
      for (const file of sessionFiles) {
        try {
          const sessionId = file.replace('.json', '');
          const filePath = getSessionFilePath(sessionId);
          const data = await readFile(filePath, 'utf8');
          const sessionData: SessionData = JSON.parse(data);
          sessions.push(sessionData);
        } catch (error) {
          console.error(`Failed to load session ${file}:`, error);
        }
      }
      
      return sessions.sort((a, b) => b.updatedAt - a.updatedAt); // Most recent first
    } catch (error) {
      console.error('Failed to list sessions:', error);
      return [];
    }
  }, [getSessionDir, getSessionFilePath]);

  const listBackendSessions = useCallback(async (target: TargetInfo): Promise<any[]> => {
    try {
      const baseUrl = appConfig.apiBaseUrl || 'http://localhost:9888';
      const endpoint = `${baseUrl}/playground/${target.type}s/${target.id}/sessions`;
      
      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`Failed to fetch sessions: ${response.statusText}`);
      }
      
      const sessions = await response.json();
      return Array.isArray(sessions) ? sessions : [];
    } catch (error) {
      console.error('Failed to list backend sessions:', error);
      return [];
    }
  }, []);

  const getSessionMetadata = useCallback(async (sessionId: string): Promise<SessionData | null> => {
    try {
      const filePath = getSessionFilePath(sessionId);
      const data = await readFile(filePath, 'utf8');
      const sessionData: SessionData = JSON.parse(data);
      return sessionData;
    } catch (error) {
      console.error(`Failed to get session metadata for ${sessionId}:`, error);
      return null;
    }
  }, [getSessionFilePath]);

  const deleteSession = useCallback(async (sessionId: string): Promise<void> => {
    try {
      const filePath = getSessionFilePath(sessionId);
      const { unlink } = await import('fs/promises');
      await unlink(filePath);
      
      if (appConfig.cliDebug) {
        console.log(`Session deleted: ${filePath}`);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      throw error;
    }
  }, [getSessionFilePath]);

  const contextValue: SessionContextType = {
    history,
    currentSessionId,
    currentTarget,
    addMessage,
    clearHistory,
    saveSession: saveSessionData,
    loadSession: loadSessionData,
    createNewSession,
    listSessions,
    listBackendSessions,
    deleteSession,
    getSessionMetadata,
    setCurrentTarget,
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};