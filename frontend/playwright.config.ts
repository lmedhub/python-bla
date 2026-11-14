import { defineConfig, devices } from "@playwright/test";

// Browser tests against the whole stack (nginx, Django, Postgres), not the dev server:
// start it first with `docker compose up --build --wait` (ADR 0016).
export default defineConfig({
  testDir: "./e2e",
  // One browser at a time: the specs share the seeded database, and login is throttled
  // to 5 a minute per IP, which parallel sign-ins would hit.
  workers: 1,
  fullyParallel: false,
  // A flaky test should fail and be fixed, not be retried until it passes.
  retries: 0,
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8080",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
