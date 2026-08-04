import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environmentMatchGlobs: [
      ["src/**/__tests__/*.test.tsx", "jsdom"],
    ],
    include: ["tests/**/*.test.ts", "src/**/__tests__/*.test.tsx"],
    globals: true,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
});
