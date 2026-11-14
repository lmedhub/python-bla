import { expect, test } from "@playwright/test";
import { ALICE, expectNoConsoleProblems, openWatchedPage, signIn, type WatchedPage } from "./support";

test.describe.configure({ mode: "serial" });

let watched: WatchedPage;

test.beforeAll(async ({ browser }) => {
  watched = await openWatchedPage(browser);
});

test.afterEach(() => {
  expectNoConsoleProblems(watched);
});

test.afterAll(async () => {
  await watched.page.close();
});

test("a signed-out visitor signs in and lands on the page they asked for", async () => {
  const { page } = watched;
  await page.goto("/tasks?status=done");
  await expect(page).toHaveURL(/\/login$/);

  await signIn(page, ALICE);

  await expect(page).toHaveURL(/\/tasks\?status=done$/);
  await expect(page.getByLabel("Status")).toHaveValue("done");
  await expect(page.getByRole("banner")).toContainText("Alice");
});

test("the session survives a reload, through the refresh cookie", async () => {
  const { page } = watched;
  await page.reload();

  await expect(page.getByRole("heading", { name: "Tasks", level: 1 })).toBeVisible();
  await expect(page.getByRole("banner")).toContainText("Alice");
});

test("signing out ends the session, also after a reload", async () => {
  const { page } = watched;
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();

  await page.reload();

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});
