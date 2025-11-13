export type ApiConfig = {
  port: number;
  bodyLimitBytes: number;
  rateLimitRps: number;
  corsOrigin: string;
  requestTimeoutMs: number;
  supportedVersions: string[]; // e.g., ["1"]
};

export function loadConfig(overrides: Partial<ApiConfig> = {}): ApiConfig {
  const cfg: ApiConfig = {
    port: Number(process.env.PORT ?? 8080),
    bodyLimitBytes: Number(process.env.BODY_LIMIT_BYTES ?? 1_000_000),
    rateLimitRps: Number(process.env.RATE_LIMIT_RPS ?? 10),
    corsOrigin: process.env.CORS_ORIGIN ?? "*",
    requestTimeoutMs: Number(process.env.REQUEST_TIMEOUT_MS ?? 15_000),
    supportedVersions: (process.env.SUPPORTED_VERSIONS ?? "1").split(",").map((s) => s.trim()).filter(Boolean)
  };
  return { ...cfg, ...overrides };
}