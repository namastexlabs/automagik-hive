import { useState, useEffect, useCallback } from 'react';
import { StreamingState } from '../types.js';

interface UseLoadingIndicatorResult {
  elapsedTime: number;
  currentLoadingPhrase: string;
}

const LOADING_PHRASES = [
  'Thinking...',
  'Processing...',
  'Analyzing...',
  'Generating response...',
  'Almost there...',
  'Just a moment...',
  'Working on it...',
  'Computing...',
];

export const useLoadingIndicator = (streamingState: StreamingState): UseLoadingIndicatorResult => {
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [currentLoadingPhrase, setCurrentLoadingPhrase] = useState<string>('');
  const [phraseIndex, setPhraseIndex] = useState<number>(0);

  const isLoading = streamingState === StreamingState.Connecting || 
                   streamingState === StreamingState.Waiting ||
                   streamingState === StreamingState.Responding;

  // Reset when loading starts
  useEffect(() => {
    if (isLoading) {
      setElapsedTime(0);
      setPhraseIndex(0);
      setCurrentLoadingPhrase(LOADING_PHRASES[0]);
    } else {
      setElapsedTime(0);
      setCurrentLoadingPhrase('');
    }
  }, [isLoading]);

  // Timer for elapsed time and phrase rotation
  useEffect(() => {
    if (!isLoading) {
      return;
    }

    const interval = setInterval(() => {
      setElapsedTime(prev => prev + 100);
      
      // Change loading phrase every 2 seconds
      if (elapsedTime % 2000 === 0 && elapsedTime > 0) {
        setPhraseIndex(prev => {
          const nextIndex = (prev + 1) % LOADING_PHRASES.length;
          setCurrentLoadingPhrase(LOADING_PHRASES[nextIndex]);
          return nextIndex;
        });
      }
    }, 100);

    return () => clearInterval(interval);
  }, [isLoading, elapsedTime]);

  return {
    elapsedTime,
    currentLoadingPhrase: isLoading ? currentLoadingPhrase : '',
  };
};