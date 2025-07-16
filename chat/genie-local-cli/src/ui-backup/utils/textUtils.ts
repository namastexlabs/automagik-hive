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