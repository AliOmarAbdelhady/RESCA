// RescueVision frontend lint rules (docs/FRONTEND.md). Locked: only the owner changes this
// file. Never silence a rule with an eslint-disable comment to get green; fix the
// code, or ask the owner for a scoped exception added here with a reason.
//
// Pinned toolchain: eslint 9 (eslint-plugin-react-native does not support 10 yet),
// typescript 6.0 (typescript-eslint supports < 6.1).
import betterTailwind from "eslint-plugin-better-tailwindcss";
import i18next from "eslint-plugin-i18next";
import reactHooks from "eslint-plugin-react-hooks";
import reactNative from "eslint-plugin-react-native";
import tseslint from "typescript-eslint";

const THEME = "packages/config/tailwind/theme.css";

// Colour literals anywhere in code: hex, rgb(), rgba(), hsl(), hsla(), oklch() (rule W1).
const COLOUR = String.raw`/#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b|\b(?:rgba?|hsla?|oklch)\s*\(/`;

const noHardCoding = {
  "no-restricted-syntax": [
    "error",
    {
      selector: `Literal[value=${COLOUR}]`,
      message: "Hard-coded colour. Use a token class (bg-surface, text-severity-critical) from the theme (W1).",
    },
    {
      selector: `TemplateElement[value.raw=${COLOUR}]`,
      message: "Hard-coded colour in a template string. Use a token (W1).",
    },
    {
      selector: "JSXAttribute[name.name='style']",
      message: "Inline style. Use token classes or a shared component variant (W1).",
    },
    {
      selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']",
      message: "Raw HTML. Render text, or use the reviewed sanitizer adapter (W11).",
    },
  ],
};

export default tseslint.config(
  { ignores: ["**/dist/**", "**/build/**", "**/.expo/**", "**/node_modules/**", "**/*.gen.ts", "packages/api/src/generated/**"] },

  // TypeScript: strict, type-aware (X1, X6).
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } },
    plugins: { "react-hooks": reactHooks, i18next, "better-tailwindcss": betterTailwind },
    settings: { "better-tailwindcss": { entryPoint: THEME } },
    rules: {
      // Errors are never swallowed (X1).
      "no-empty": ["error", { allowEmptyCatch: false }],
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/only-throw-error": "error",
      "@typescript-eslint/prefer-promise-reject-errors": "error",
      "no-console": ["error", { allow: ["warn", "error"] }],
      eqeqeq: "error",

      // Hooks are called correctly.
      ...reactHooks.configs.recommended.rules,

      // No user-visible text in code: every string goes through t() (W3).
      "i18next/no-literal-string": [
        "error",
        { mode: "jsx-only", "jsx-attributes": { include: ["title", "label", "placeholder", "alt", "aria-label", "aria-description"] } },
      ],

      // Only token classes exist; no arbitrary values like bg-[#fff] or p-[13px] (W1).
      "better-tailwindcss/no-unknown-classes": "error",
      "better-tailwindcss/no-concatenated-classes": "error",
      // ms-/me-/ps-/pe- instead of ml-/mr-/pl-/pr- so Arabic (RTL) layouts mirror (W3).
      "better-tailwindcss/enforce-logical-properties": "error",
      "better-tailwindcss/no-conflicting-classes": "error",
      "better-tailwindcss/no-duplicate-classes": "error",
      "better-tailwindcss/no-restricted-classes": [
        "error",
        { restrict: [{ pattern: String.raw`^.*\[.+\].*$`, message: "Arbitrary Tailwind value. Add or use a token in the theme (W1)." }] },
      ],

      ...noHardCoding,
    },
  },

  // Apps compose shared components and generated hooks; they never reach underneath (W2, W4).
  {
    files: ["apps/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          paths: [{ name: "axios", message: "Use the generated client in @rescuevision/api (W4)." }],
          patterns: [
            { group: ["@radix-ui/*"], message: "Use the wrapped component from @rescuevision/ui (W2)." },
            { group: ["**/*.mock", "**/*.mock.*", "**/mocks/**"], message: "No fake data in screens (W4)." },
            { group: ["../../*"], message: "Import through the package or feature entry point, not deep relative paths." },
          ],
        },
      ],
      "no-restricted-globals": ["error", { name: "fetch", message: "Use the generated client in @rescuevision/api (W4)." }],
    },
  },

  // Mobile: same rules plus React Native specifics (M1).
  {
    files: ["apps/mobile/**/*.{ts,tsx}"],
    plugins: { "react-native": reactNative },
    rules: {
      "react-native/no-color-literals": "error",
      "react-native/no-inline-styles": "error",
      "react-native/no-raw-text": "error",
      "react-native/no-unused-styles": "error",
    },
  },

  // Tests and stories may use literal strings and fixtures.
  {
    files: ["**/*.test.{ts,tsx}", "**/*.spec.{ts,tsx}", "**/*.stories.{ts,tsx}"],
    rules: { "i18next/no-literal-string": "off", "no-restricted-imports": "off" },
  },
);
