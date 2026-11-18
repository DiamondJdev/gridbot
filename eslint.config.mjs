import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default [
  {
    ignores: [
      "**/dist/**",
      "**/artifacts/**",
      "**/.superpowers/**",
      "**/.venv/**",
      "**/build/**",
      "**/install/**",
      "**/log/**",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["gateway/src/main.ts"],
    languageOptions: { globals: { console: "readonly" } },
  },
];
