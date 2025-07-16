import React, { createContext, useContext, useState } from 'react';
import { StreamingState } from '../types.js';

interface StreamingContextType {
  streamingState: StreamingState;
  setStreamingState: (state: StreamingState) => void;
  isStreaming: boolean;
}

const StreamingContext = createContext<StreamingContextType | undefined>(undefined);

export const useStreamingContext = (): StreamingContextType => {
  const context = useContext(StreamingContext);
  if (!context) {
    throw new Error('useStreamingContext must be used within a StreamingProvider');
  }
  return context;
};

interface StreamingProviderProps {
  children: React.ReactNode;
}

export const StreamingProvider: React.FC<StreamingProviderProps> = ({ children }) => {
  const [streamingState, setStreamingState] = useState<StreamingState>(StreamingState.Idle);

  const isStreaming = streamingState === StreamingState.Responding || 
                     streamingState === StreamingState.Waiting ||
                     streamingState === StreamingState.Connecting;

  const contextValue: StreamingContextType = {
    streamingState,
    setStreamingState,
    isStreaming,
  };

  return (
    <StreamingContext.Provider value={contextValue}>
      {children}
    </StreamingContext.Provider>
  );
};