import react from "@vitejs/plugin-react";
import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    // The browser talks to one origin: no CORS, and the refresh cookie (path /api/v1/auth)
    // is sent as in production, where nginx does the same proxying.
    proxy: { "/api": "http://localhost:8000" },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    // Playwright runs these in a real browser against the whole stack (npm run e2e).
    exclude: [...configDefaults.exclude, "e2e/**"],
    // West of UTC, so a date shown one day early (the classic "new Date('2026-11-12')" bug)
    // fails the tests instead of only users in the Americas.
    env: { TZ: "America/Sao_Paulo" },
  },
});
