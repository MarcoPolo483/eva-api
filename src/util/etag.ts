export function weakEtagFromString(s: string): string {
  // Simple non-cryptographic hash for ETag W/ prefix
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h << 5) - h + s.charCodeAt(i);
    h |= 0;
  }
  return `W/"${(h >>> 0).toString(16)}-${s.length}"`;
}