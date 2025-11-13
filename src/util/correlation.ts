export function getOrCreateCorrelationId(headers: Record<string, string | string[] | undefined>): string {
  const v = headers["x-correlation-id"] ?? headers["X-Correlation-Id" as any];
  if (Array.isArray(v)) return v[0];
  if (typeof v === "string" && v) return v;
  return generateId();
}

export function generateId(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
}