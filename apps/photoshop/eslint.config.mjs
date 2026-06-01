// ESLint flat config for the Photoshop UXP plugin.
//
// Stacks typescript-eslint's `strictTypeChecked` preset on top of the
// `recommendedTypeChecked` baseline so the panels get the full
// type-aware rule set: no-unsafe-*, no-misused-promises,
// require-await, etc. Pairs with the `exactOptionalPropertyTypes` +
// `noUncheckedIndexedAccess` gate in tsconfig.json.
//
// Run with: pnpm exec eslint src

import tseslint from "typescript-eslint";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import jsxA11yPlugin from "eslint-plugin-jsx-a11y";

export default tseslint.config(
    {
        ignores: [
            "dist/**",
            "out/**",
            "node_modules/**",
            "uxp-plugin-tests/**",
            // Adobe React UXP starter adapter. Carries `@ts-nocheck`
            // because the Symbol-keyed private fields + untyped Component
            // contract are what `entrypoints.setup({ panels: ... })`
            // requires; rewriting to typed JS surfaces "No value
            // specified for panel key" at runtime (see commit 985e915).
            // Vendored verbatim; never edit by hand.
            "src/controllers/PanelController.tsx",
            // Generated codegen output; tsc gates the shapes already.
            "src/schema_bindings/**",
        ],
    },
    ...tseslint.configs.strictTypeChecked,
    ...tseslint.configs.stylisticTypeChecked,
    {
        languageOptions: {
            parserOptions: {
                projectService: true,
                tsconfigRootDir: import.meta.dirname,
            },
        },
        plugins: {
            react: reactPlugin,
            "react-hooks": reactHooksPlugin,
            "jsx-a11y": jsxA11yPlugin,
        },
        settings: {
            react: { version: "16.14" },
        },
        rules: {
            ...reactPlugin.configs.recommended.rules,
            // v7 ships the flat-config preset under configs.flat; the
            // legacy configs.recommended path is retained but the flat
            // entry is the idiomatic source for flat config.
            ...reactHooksPlugin.configs.flat.recommended.rules,
            ...jsxA11yPlugin.flatConfigs.recommended.rules,
            "react/react-in-jsx-scope": "off",
            "react/jsx-uses-react": "off",
        },
    },
    {
        // Stylistic rules retired from the global preset. Each
        // disabled rule is style / preference, not type safety:
        //
        // - restrict-template-expressions: forces explicit `String(n)`
        //   wrapping for numeric template interpolations. The runtime
        //   conversion is unambiguous; the wrap is just noise.
        // - no-dynamic-delete: the generic `delete changes[key]` in
        //   the typed-diff helper (Details.tsx) is the documented
        //   `Partial<T>` clear pattern; the rule's recommendation
        //   (assign undefined) regresses `exactOptionalPropertyTypes`.
        // - no-invalid-void-type: the Photoshop notification API
        //   genuinely returns `void` in the legacy build, so the
        //   union `Promise<X> | X | void` reflects the actual API.
        // - array-type: T[] vs Array<T> is style only.
        rules: {
            "@typescript-eslint/restrict-template-expressions": "off",
            "@typescript-eslint/no-dynamic-delete": "off",
            "@typescript-eslint/no-invalid-void-type": "off",
            "@typescript-eslint/array-type": "off",
        },
    },
    {
        // Vitest tests bring their own typing layer; relax a few rules
        // that fight unit-test idioms (mock-injected `any` from vi.mock,
        // shallow stubs).
        files: ["**/*.test.ts", "**/*.test.tsx", "tests/**"],
        rules: {
            "@typescript-eslint/no-unsafe-assignment": "off",
            "@typescript-eslint/no-unsafe-member-access": "off",
            "@typescript-eslint/no-unsafe-call": "off",
            "@typescript-eslint/no-explicit-any": "off",
        },
    },
);
