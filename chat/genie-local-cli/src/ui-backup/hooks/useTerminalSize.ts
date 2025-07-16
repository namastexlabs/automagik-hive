import { useState, useEffect } from 'react';
import { useStdout } from 'ink';

interface TerminalSize {
  rows: number;
  columns: number;
}

export const useTerminalSize = (): TerminalSize => {
  const { stdout } = useStdout();
  const [size, setSize] = useState<TerminalSize>({
    rows: stdout.rows || 24,
    columns: stdout.columns || 80,
  });

  useEffect(() => {
    const updateSize = () => {
      setSize({
        rows: stdout.rows || 24,
        columns: stdout.columns || 80,
      });
    };

    // Update size when terminal is resized
    stdout.on('resize', updateSize);

    // Initial size
    updateSize();

    return () => {
      stdout.off('resize', updateSize);
    };
  }, [stdout]);

  return size;
};