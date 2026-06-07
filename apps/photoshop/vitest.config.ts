import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

// Resolve the UXP host mocks so api modules that import { app, ... } from
// "photoshop" / "uxp" load under plain vitest - the real modules are host
// globals that only exist inside Photoshop.
const mock = (name: string): string =>
  fileURLToPath(new URL(`./uxp-plugin-tests/__mocks__/${name}`, import.meta.url));

// Test discovery stays on Vitest defaults (**/*.test.ts[x]); this config
// adds the host-mock aliases and coverage so the Sonar scan has an lcov
// report to import.
export default defineConfig({
  test: {
    alias: {
      photoshop: mock("photoshop.ts"),
      uxp: mock("uxp.ts"),
    },
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
