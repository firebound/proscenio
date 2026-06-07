import { defineConfig } from "vitest/config";

// Test discovery stays on Vitest defaults (**/*.test.ts[x]); this config
// only adds coverage so the Sonar scan has an lcov report to import.
export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      reportsDirectory: "coverage",
      // Score the plugin source only; tests, the build output, and config
      // files are not the code under test.
      include: ["src/**/*.{ts,tsx}"],
      // entry.ts is the @ts-nocheck UXP host shim (the one typed-gate
      // exemption); .d.ts files are ambient declarations, not executable;
      // schema_bindings/ is generated (kept out of the Sonar scan too, so
      // listing it here keeps the lcov report free of unresolvable paths).
      exclude: ["src/entry.ts", "src/**/*.d.ts", "src/schema_bindings/**"],
    },
  },
});
