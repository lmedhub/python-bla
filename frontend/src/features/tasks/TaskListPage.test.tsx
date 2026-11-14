import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { alice, bob, makeTask } from "../../test/data";
import { errorBody, signedInAs, taskListReturns, usersAre } from "../../test/handlers";
import { renderApp } from "../../test/render";
import { server } from "../../test/server";

/** The list item of the task with this title. */
function taskItem(title: string): HTMLElement {
  const item = screen.getByRole("heading", { name: title }).closest("li");
  if (item === null) throw new Error(`No list item for "${title}".`);
  return item;
}

beforeEach(() => {
  signedInAs(alice);
  usersAre([alice, bob]);
});

describe("the task list", () => {
  it("shows each task's title, status, due date and assignee", async () => {
    taskListReturns([
      makeTask({ title: "Pay invoices", status: "in_progress", due_date: "2026-11-20", assignee: bob.id }),
      makeTask({ title: "Plan offsite", due_date: null, assignee: null }),
    ]);

    renderApp("/tasks");

    expect(screen.getByRole("status")).toHaveTextContent("Loading");
    const invoices = await screen.findByRole("heading", { name: "Pay invoices" });
    const item = within(invoices.closest("li") ?? document.body);
    expect(item.getByText("In progress")).toBeInTheDocument();
    expect(item.getByText("Nov 20, 2026")).toBeInTheDocument();
    expect(await item.findByText("Bob")).toBeInTheDocument();
    const offsite = within(taskItem("Plan offsite"));
    expect(offsite.getByText("No due date")).toBeInTheDocument();
    expect(offsite.getByText("Unassigned")).toBeInTheDocument();
  });

  it("marks overdue tasks", async () => {
    taskListReturns([
      makeTask({ title: "Late", due_date: "2026-11-01", is_overdue: true }),
      makeTask({ title: "On time", due_date: "2026-12-01", is_overdue: false }),
    ]);

    renderApp("/tasks");

    await screen.findByRole("heading", { name: "Late" });
    expect(within(taskItem("Late")).getByText("Overdue")).toBeInTheDocument();
    expect(within(taskItem("On time")).queryByText("Overdue")).not.toBeInTheDocument();
  });

  it("invites to create the first task when there are none", async () => {
    taskListReturns([]);

    renderApp("/tasks");

    expect(await screen.findByText("No tasks yet.")).toBeInTheDocument();
  });

  it("says when no task matches the filters", async () => {
    taskListReturns([]);

    renderApp("/tasks?status=done");

    expect(await screen.findByText("No tasks match these filters.")).toBeInTheDocument();
  });

  it("shows an error with a way to try again", async () => {
    taskListReturns([makeTask({ title: "Pay invoices" })]);
    // Added last, so MSW tries it first: the first request fails, the retry succeeds.
    server.use(
      http.get(
        "/api/v1/tasks",
        () =>
          HttpResponse.json(errorBody("server_error", "A server error occurred."), { status: 500 }),
        { once: true },
      ),
    );
    const { user } = renderApp("/tasks");

    expect(await screen.findByRole("alert")).toHaveTextContent("A server error occurred.");
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "Pay invoices" })).toBeInTheDocument();
  });

  it("goes to the login page when the session ends while browsing", async () => {
    // The page load restores the session once; after that the refresh token is gone.
    // MSW tries handlers in the order given, so the one-time success must come first.
    server.use(
      http.post(
        "/api/v1/auth/refresh",
        () => HttpResponse.json({ access: "access-token", user: alice }),
        { once: true },
      ),
      http.post("/api/v1/auth/refresh", () =>
        HttpResponse.json(errorBody("not_authenticated", "Session expired."), { status: 401 }),
      ),
      http.get("/api/v1/tasks", () =>
        HttpResponse.json(errorBody("not_authenticated", "Token expired."), { status: 401 }),
      ),
    );

    renderApp("/tasks");

    // Signed in first (the header shows the user), then sent to the login page.
    expect(await screen.findByText("Alice")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });
});

describe("filters", () => {
  it("are read from the URL and sent to the API", async () => {
    const requested = taskListReturns([]);

    renderApp(
      "/tasks?status=done&assignee=me&due_after=2026-11-01&due_before=2026-11-30&overdue=false&page=2",
    );

    await screen.findByText("No tasks match these filters.");
    expect(Object.fromEntries(requested[0]?.searchParams ?? [])).toEqual({
      status: "done",
      assignee: "me",
      due_after: "2026-11-01",
      due_before: "2026-11-30",
      overdue: "false",
      page: "2",
      page_size: "10",
    });
    expect(screen.getByLabelText("Status")).toHaveValue("done");
    expect(screen.getByLabelText("Assignee")).toHaveValue("me");
    expect(screen.getByLabelText("Due after")).toHaveValue("2026-11-01");
    expect(screen.getByLabelText("Due before")).toHaveValue("2026-11-30");
    expect(screen.getByLabelText("Overdue")).toHaveValue("false");
  });

  it("update the URL and go back to page 1 when changed", async () => {
    const requested = taskListReturns([makeTask({ title: "Pay invoices" })], 30);
    const { user } = renderApp("/tasks?page=3");
    await screen.findByRole("heading", { name: "Pay invoices" });

    await user.selectOptions(screen.getByLabelText("Status"), "In progress");
    await user.selectOptions(await screen.findByLabelText("Assignee"), "Bob");

    expect(screen.getByTestId("current-url")).toHaveTextContent(
      `/tasks?status=in_progress&assignee=${String(bob.id)}`,
    );
    expect(requested.at(-1)?.searchParams.get("assignee")).toBe(String(bob.id));
    expect(requested.at(-1)?.searchParams.get("page")).toBe("1");
  });

  it("can all be cleared at once", async () => {
    taskListReturns([]);
    const { user } = renderApp("/tasks?status=done&overdue=true");

    await user.click(await screen.findByRole("button", { name: "Clear filters" }));

    expect(screen.getByTestId("current-url")).toHaveTextContent(/^\/tasks$/);
    expect(await screen.findByText("No tasks yet.")).toBeInTheDocument();
  });
});

describe("pagination", () => {
  it("moves between pages through the URL", async () => {
    const requested = taskListReturns([makeTask({ title: "Pay invoices" })], 25);
    const { user } = renderApp("/tasks");

    const pagination = await screen.findByRole("navigation", { name: "Pagination" });
    expect(within(pagination).getByText("Page 1 of 3")).toBeInTheDocument();
    expect(within(pagination).getByRole("button", { name: "Previous page" })).toBeDisabled();

    await user.click(within(pagination).getByRole("button", { name: "Next page" }));

    expect(screen.getByTestId("current-url")).toHaveTextContent("/tasks?page=2");
    expect(await within(pagination).findByText("Page 2 of 3")).toBeInTheDocument();
    expect(requested.at(-1)?.searchParams.get("page")).toBe("2");
  });

  it("is hidden when everything fits on one page", async () => {
    taskListReturns([makeTask({ title: "Pay invoices" })]);

    renderApp("/tasks");

    await screen.findByRole("heading", { name: "Pay invoices" });
    expect(screen.queryByRole("navigation", { name: "Pagination" })).not.toBeInTheDocument();
  });

  it("offers a way back from a page past the end", async () => {
    taskListReturns([], 5);
    const { user } = renderApp("/tasks?page=9");

    await user.click(await screen.findByRole("button", { name: "Go to the first page" }));

    expect(screen.getByTestId("current-url")).toHaveTextContent(/^\/tasks$/);
  });
});
