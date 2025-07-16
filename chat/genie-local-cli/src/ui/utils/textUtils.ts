/**
 * Unicode-aware text utilities copied from gemini-cli
 * Work at the code-point level rather than UTF-16 code units 
 * so that surrogate-pair emoji count as one "column"
 */

export function toCodePoints(str: string): string[] {
  // [...str] or Array.from both iterate by UTF-32 code point, handling
  // surrogate pairs correctly.
  return Array.from(str);
}

export function cpLen(str: string): number {
  return toCodePoints(str).length;
}

export function cpSlice(str: string, start: number, end?: number): string {
  // Slice by code-point indices and re-join.
  const arr = toCodePoints(str).slice(start, end);
  return arr.join('');
}

/**
 * Calculate the width (in terminal columns) of ASCII art.
 */
export function getAsciiArtWidth(asciiArt: string): number {
  const lines = asciiArt.split('\n').filter(line => line.trim() !== '');
  if (lines.length === 0) return 0;
  
  // Return the width of the longest line
  return Math.max(...lines.map(line => line.length));
}

/**
 * Shorten a path for display.
 */
export function shortenPath(path: string, maxLength: number): string {
  if (path.length <= maxLength) {
    return path;
  }
  
  const parts = path.split('/');
  if (parts.length <= 1) {
    return path.slice(-maxLength);
  }
  
  // Keep the last part and truncate from the middle
  const lastPart = parts[parts.length - 1];
  const remaining = maxLength - lastPart.length - 3; // 3 for "..."
  
  if (remaining <= 0) {
    return '...' + lastPart.slice(-(maxLength - 3));
  }
  
  const firstParts = parts.slice(0, -1).join('/');
  if (firstParts.length <= remaining) {
    return firstParts + '/' + lastPart;
  }
  
  return firstParts.slice(0, remaining) + '.../' + lastPart;
}

/**
 * Replace home directory with tilde.
 */
export function tildeifyPath(path: string): string {
  const homedir = process.env.HOME || process.env.USERPROFILE || '';
  if (homedir && path.startsWith(homedir)) {
    return '~' + path.slice(homedir.length);
  }
  return path;
}