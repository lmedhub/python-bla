import { expect, test } from "@playwright/test";
import {
  ALICE,
  expectNoConsoleProblems,
  isoDateFromToday,
  openWatchedPage,
  signIn,
  taskItem,
  type WatchedPage,
} from "./support";

// One task's life, as its creator: create, find, edit, complete, delete. The task gets a
// unique title and a due date far from the seeded ones, so the date filters isolate it.
test.describe.configure({ mode: "serial" });

const title = `E2E task ${String(Date.now())}`;
const editedTitle = `${title} (edited)`;
const dueDate = isoDateFromToday(400);

let watched: WatchedPage;
let filteredUrl: string;

test.beforeAll(async ({ browser }) => {
  watched = await openWatchedPage(browser);
  await watched.page.goto("/login");
  await signIn(watched.page, ALICE);
});

test.afterEach(() => {
  expectNoConsoleProblems(watched);
});

test.afterAll(async () => {
  await watched.page.close();
});

test("overdue tasks carry a badge, done ones do not", async () => {
  const { page } = watched;
  await expect(taskItem(page, "Prepare Q4 budget review")).toContainText("Overdue");
  await expect(taskItem(page, "Send November invoices")).not.toContainText("Overdue");
});

test("a new task can be found with the due date filters, also after a reload", async () => {
  const { page } = watched;
  await page.getByRole("link", { name: "New task" }).click();
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Description").fill("Created by the browser tests.");
  await page.getByLabel("Due date").fill(dueDate);
  await page.getByLabel("Assignee").selectOption({ label: "Bob" });
  await page.getByRole("button", { name: "Create task" }).click();
  await expect(page).toHaveURL(/\/tasks$/);

  await page.getByLabel("Due after").fill(dueDate);
  await page.getByLabel("Due before").fill(dueDate);
  await expect(page).toHaveURL(new RegExp(`due_after=${dueDate}&due_before=${dueDate}`));
  await expect(taskItem(page, title)).toContainText("To do");
  await expect(taskItem(page, title)).toContainText("Bob");
  filteredUrl = page.url();

  await page.reload();

  await expect(page.getByLabel("Due after")).toHaveValue(dueDate);
  await expect(page.getByRole("listitem")).toHaveCount(1);
  await expect(taskItem(page, title)).toBeVisible();
});

test("the creator edits the task", async () => {
  const { page } = watched;
  await taskItem(page, title).getByRole("link", { name: "Edit" }).click();
  await expect(page.getByRole("heading", { name: "Edit task" })).toBeVisible();
  await expect(page.getByLabel("Title")).toHaveValue(title);

  await page.getByLabel("Title").fill(editedTitle);
  await page.getByLabel("Status").selectOption({ label: "In progress" });
  await page.getByRole("button", { name: "Save changes" }).click();

  await expect(page).toHaveURL(/\/tasks$/);
  await page.goto(filteredUrl);
  await expect(taskItem(page, editedTitle)).toContainText("In progress");
});

test("marking the task done is saved", async () => {
  const { page } = watched;
  const item = taskItem(page, editedTitle);
  await item.getByRole("button", { name: "Mark done" }).click();

  await expect(item.getByRole("button", { name: "Reopen" })).toBeVisible();
  await page.reload();
  await expect(taskItem(page, editedTitle)).toContainText("Done");
});

test("delete asks first, and Esc cancels", async () => {
  const { page } = watched;
  const item = taskItem(page, editedTitle);
  const dialog = page.getByRole("dialog", { name: `Delete "${editedTitle}"?` });

  await item.getByRole("button", { name: "Delete" }).click();
  await expect(dialog).toBeVisible();
  // Focus starts on the safe choice.
  await expect(dialog.getByRole("button", { name: "Cancel" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(item).toBeVisible();

  await item.getByRole("button", { name: "Delete" }).click();
  await dialog.getByRole("button", { name: "Delete task" }).click();

  await expect(item).toBeHidden();
  await expect(page.getByText("No tasks match these filters.")).toBeVisible();
});

test("the list fits a 320 px wide screen", async () => {
  const { page } = watched;
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto("/tasks");
  await expect(page.getByRole("link", { name: "New task" })).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, "horizontal scroll in pixels").toBe(0);
});
