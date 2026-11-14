import { expect, type Browser, type Locator, type Page } from "@playwright/test";

// Each spec file signs in once and shares one page across its tests (ADR 0016): login is
// throttled to 5 a minute, and a saved session cannot be reused because the refresh token
// rotates on every use.

/** A page that records console warnings, console errors and uncaught exceptions. */
export interface WatchedPage {
  page: Page;
  problems: string[];
}

export async function openWatchedPage(browser: Browser): Promise<WatchedPage> {
  const page = await browser.newPage();
  const problems: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "warning" || message.type() === "error") {
      problems.push(`${message.type()}: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    problems.push(`uncaught: ${error.message}`);
  });
  return { page, problems };
}

/** HANDOFF: zero console warnings or errors. Run after every test; clears the record. */
export function expectNoConsoleProblems(watched: WatchedPage): void {
  const problems = watched.problems.splice(0);
  expect(problems, "browser console warnings and errors").toEqual([]);
}

export const ALICE = "alice@example.com";
export const BOB = "bob@example.com";

function demoPassword(): string {
  const password = process.env.DEMO_PASSWORD;
  if (!password) {
    throw new Error("Set DEMO_PASSWORD to the stack's demo password (see .env).");
  }
  return password;
}

/** Signs in on the login page the browser is on, and waits for the task list. */
export async function signIn(page: Page, email: string): Promise<void> {
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(demoPassword());
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Tasks", level: 1 })).toBeVisible();
}

/** The list item of the task with this exact title. */
export function taskItem(page: Page, title: string): Locator {
  return page
    .getByRole("listitem")
    .filter({ has: page.getByRole("heading", { name: title, exact: true }) });
}

/** A local date `days` from today, as "YYYY-MM-DD" (the date inputs' format). */
export function isoDateFromToday(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${String(date.getFullYear())}-${month}-${day}`;
}
