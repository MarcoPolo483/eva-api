import type { IncomingMessage } from "http";

export type AuthConfig = {
  apiKey?: string;
  metricsPublic?: boolean;
  ssePublic?: boolean;
};

export function isPublicRoute(url: string, method: string, cfg: AuthConfig): boolean {
  if (cfg.metricsPublic && url.startsWith("/ops/metrics")) return true;
  if (cfg.ssePublic && url.startsWith("/rag/events")) return true;
  return false;
}

export async function authorize(req: IncomingMessage, cfg: AuthConfig): Promise<boolean> {
  const key = cfg.apiKey;
  if (!key) return true; // no auth configured
  const hdr = (req.headers["x-api-key"] as string) || "";
  if (hdr && hdr === key) return true;
  const auth = (req.headers["authorization"] as string) || "";
  if (auth.startsWith("Bearer ")) {
    const token = auth.slice("Bearer ".length);
    if (token === key) return true;
  }
  return false;
}