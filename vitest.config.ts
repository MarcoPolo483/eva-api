import { defineConfig } from "vitest/config";
import { fileURLToPath } from "url";
import { dirname, resolve as pathResolve } from "path";
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
export default defineConfig({
  resolve: {
    alias: {
      // Map external monorepo package to local test stub to avoid cross-repo coupling in tests
      "eva-core": pathResolve(__dirname, "src/test-stubs/eva-core.ts"),
    },
  },
  optimizeDeps: {
    exclude: ["eva-core"],
  },
  test: {
    // Inline eva-core so alias takes effect in Vitest
    deps: { inline: ["eva-core"] },
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov", "html"],
      lines: 80,
      functions: 80,
      statements: 80,
      branches: 70,
      exclude: ["src/index.ts"],
    },
    environment: "node",
    include: ["src/__tests__/**/*.test.ts"],
    globals: true
  }
});