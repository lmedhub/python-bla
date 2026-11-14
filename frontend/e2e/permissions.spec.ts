import { expect, test } from "@playwright/test";
import { BOB, expectNoConsoleProblems, openWatchedPage, signIn, taskItem, type WatchedPage } from "./support";

// Bob looks at seeded in-progress tasks (one page, read only): one he created, one assigned
// to him, and one that is neither. The API enforces the same rules; this checks the UI
// offers only what he may do.
test.describe.configure({ mode: "serial" });

let watched: WatchedPage;

test.beforeAll(async ({ browser }) => {
  watched = await openWatchedPage(browser);
  await watched.page.goto("/login");
  await signIn(watched.page, BOB);
  await watched.page.goto("/tasks?status=in_progress");
});

test.afterEach(() => {
  expectNoConsoleProblems(watched);
});

test.afterAll(async () => {
  await watched.page.close();
});

test("the creator may do everything", async () => {
  const item = taskItem(watched.page, "Update privacy notice");
  await expect(item.getByRole("button", { name: "Mark done" })).toBeEnabled();
  await expect(item.getByRole("link", { name: "Edit" })).toBeVisible();
  await expect(item.getByRole("button", { name: "Delete" })).toBeEnabled();
});

test("the assignee may change the status only", async () => {
  const item = taskItem(watched.page, "Migrate CI to new runners");
  await expect(item.getByRole("button", { name: "Mark done" })).toBeEnabled();
  await expect(item.getByRole("button", { name: "Edit" })).toBeDisabled();
  await expect(item.getByRole("button", { name: "Delete" })).toBeDisabled();
});

test("anyone else may only read", async () => {
  const item = taskItem(watched.page, "Book venue for team offsite");
  await expect(item.getByRole("button", { name: "Mark done" })).toBeDisabled();
  await expect(item.getByRole("button", { name: "Edit" })).toBeDisabled();
  await expect(item.getByRole("button", { name: "Delete" })).toBeDisabled();
});

test("the edit page refuses a task the user did not create", async () => {
  const { page } = watched;
  // The disabled button has no link; reach the page by its URL, as a shared link would.
  // The task's id comes from the list response the page itself receives.
  const listResponse = page.waitForResponse((response) => response.url().includes("/api/v1/tasks?"));
  await page.goto("/tasks?status=in_progress");
  const body = (await (await listResponse).json()) as { results: { id: number; title: string }[] };
  const task = body.results.find((t) => t.title === "Migrate CI to new runners");
  expect(task).toBeDefined();

  await page.goto(`/tasks/${String(task?.id)}/edit`);

  await expect(page.getByText("Only the person who created this task can edit it.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Save changes" })).toHaveCount(0);
});
