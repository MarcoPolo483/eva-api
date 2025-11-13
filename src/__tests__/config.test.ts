import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { loadConfig } from "../util/config.js";

describe("loadConfig", () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("loads default config when no env vars set", () => {
    delete process.env.PORT;
    delete process.env.BODY_LIMIT_BYTES;
    delete process.env.RATE_LIMIT_RPS;
    delete process.env.CORS_ORIGIN;
    delete process.env.REQUEST_TIMEOUT_MS;
    delete process.env.SUPPORTED_VERSIONS;

    const cfg = loadConfig();
    expect(cfg.port).toBe(8080);
    expect(cfg.bodyLimitBytes).toBe(1_000_000);
    expect(cfg.rateLimitRps).toBe(10);
    expect(cfg.corsOrigin).toBe("*");
    expect(cfg.requestTimeoutMs).toBe(15_000);
    expect(cfg.supportedVersions).toEqual(["1"]);
  });

  it("loads config from environment variables", () => {
    process.env.PORT = "3000";
    process.env.BODY_LIMIT_BYTES = "5000";
    process.env.RATE_LIMIT_RPS = "100";
    process.env.CORS_ORIGIN = "https://example.com";
    process.env.REQUEST_TIMEOUT_MS = "30000";
    process.env.SUPPORTED_VERSIONS = "1,2,3";

    const cfg = loadConfig();
    expect(cfg.port).toBe(3000);
    expect(cfg.bodyLimitBytes).toBe(5000);
    expect(cfg.rateLimitRps).toBe(100);
    expect(cfg.corsOrigin).toBe("https://example.com");
    expect(cfg.requestTimeoutMs).toBe(30000);
    expect(cfg.supportedVersions).toEqual(["1", "2", "3"]);
  });

  it("applies overrides", () => {
    const cfg = loadConfig({ port: 9999, corsOrigin: "https://override.com" });
    expect(cfg.port).toBe(9999);
    expect(cfg.corsOrigin).toBe("https://override.com");
    expect(cfg.bodyLimitBytes).toBe(1_000_000); // default
  });
});
