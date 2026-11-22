import next from "eslint-config-next";

export default [
  ...next,
  { ignores: [".next*/**", "storybook-static/**", "node_modules/**", "playwright-report/**", "test-results/**"] },
  {
    rules: {
      // Jedyne miejsce wywołań sieciowych: src/lib/api. Reszta kodu nie używa fetch.
      "no-restricted-globals": ["error", { name: "fetch", message: "Używaj klienta z src/lib/api (useApi/hooki)." }],
    },
  },
  { files: ["src/lib/api/**"], rules: { "no-restricted-globals": "off" } },
];
