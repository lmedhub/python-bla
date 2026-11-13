import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { alice, bob, makeTask } from "../../test/data";
import { errorBody, signedInAs, taskListReturns, usersAre } from "../../test/handlers";
import { renderApp } from "../../test/render";
import { server } from "../../test/server";

/** Records the JSON bodies sent to `method path`, answering with `answer`. */
function capture(method: "post" | "patch", path: string, answer: () => Response): unknown[] {
  const bodies: unknown[] = [];
  server.use(
    http[method](path, async ({ request }) => {
      bodies.push(await request.json());
      return answer();
    }),
  );
  return bodies;
}

beforeEach(() => {
  signedInAs(alice);
  usersAre([alice, bob]);
  taskListReturns([]);
});

describe("creating a task", () => {
  it("sends the form and goes back to the list", async () => {
    const created = makeTask({ title: "Pay invoices" });
    const bodies = capture("post", "/api/v1/tasks", () => HttpResponse.json(created, { status: 201 }));
    const { user } = renderApp("/tasks");

    await user.click(await screen.findByRole("link", { name: "New task" }));
    expect(await screen.findByRole("heading", { name: "New task" })).toBeInTheDocument();
    await user.type(screen.getByLabelText("Title"), "Pay invoices");
    await user.type(screen.getByLabelText("Description"), "Before Friday");
    await user.type(screen.getByLabelText("Due date"), "2026-11-20");
    await user.selectOptions(await screen.findByLabelText("Assignee"), "Bob");
    await user.click(screen.getByRole("button", { name: "Create task" }));

    expect(await screen.findByRole("heading", { name: "Tasks" })).toBeInTheDocument();
    expect(bodies).toEqual([
      { title: "Pay invoices", description: "Before Friday", due_date: "2026-11-20", assignee: bob.id },
    ]);
  });

  it("sends no due date and no assignee when left empty", async () => {
    const bodies = capture("post", "/api/v1/tasks", () =>
      HttpResponse.json(makeTask(), { status: 201 }),
    );
    const { user } = renderApp("/tasks/new");

    await user.type(await screen.findByLabelText("Title"), "Plan offsite");
    await user.click(screen.getByRole("button", { name: "Create task" }));

    await screen.findByRole("heading", { name: "Tasks" });
    expect(bodies).toEqual([{ title: "Plan offsite", description: "", due_date: null, assignee: null }]);
  });

  it("shows the server's errors next to the fields they belong to", async () => {
    capture("post", "/api/v1/tasks", () =>
      HttpResponse.json(
        errorBody("invalid_input", "Invalid input.", {
          title: ["This field may not be blank."],
          due_date: ["Enter a valid date."],
        }),
        { status: 400 },
      ),
    );
    const { user } = renderApp("/tasks/new");

    // Input the browser accepts (a past date would be blocked by the picker's min first).
    await user.type(await screen.findByLabelText("Title"), "   ");
    await user.type(screen.getByLabelText("Due date"), "2099-01-01");
    await user.click(screen.getByRole("button", { name: "Create task" }));

    const title = await screen.findByLabelText("Title");
    expect(await screen.findByText("This field may not be blank.")).toBeInTheDocument();
    expect(title).toHaveAttribute("aria-invalid", "true");
    expect(title).toHaveAccessibleDescription("This field may not be blank.");
    expect(screen.getByLabelText("Due date")).toHaveAccessibleDescription("Enter a valid date.");
    expect(screen.getByRole("heading", { name: "New task" })).toBeInTheDocument();
  });

  it("can be cancelled", async () => {
    const { user } = renderApp("/tasks/new");

    await user.click(await screen.findByRole("link", { name: "Cancel" }));

    expect(await screen.findByRole("heading", { name: "Tasks" })).toBeInTheDocument();
  });
});

describe("editing a task", () => {
  const task = makeTask({
    title: "Pay invoices",
    description: "Before Friday",
    due_date: "2026-11-20",
    assignee: bob.id,
    created_by: alice.id,
    version: 3,
  });
  const taskUrl = `/api/v1/tasks/${String(task.id)}`;
  const editPath = `/tasks/${String(task.id)}/edit`;

  it("starts from the saved task and sends the version it was read at", async () => {
    server.use(http.get(taskUrl, () => HttpResponse.json(task)));
    const bodies = capture("patch", taskUrl, () => HttpResponse.json({ ...task, version: 4 }));
    const { user } = renderApp(editPath);

    const title = await screen.findByLabelText("Title");
    expect(title).toHaveValue("Pay invoices");
    expect(screen.getByLabelText("Description")).toHaveValue("Before Friday");
    expect(screen.getByLabelText("Due date")).toHaveValue("2026-11-20");
    expect(screen.getByLabelText("Status")).toHaveValue("todo");
    await user.clear(title);
    await user.type(title, "Pay all invoices");
    await user.selectOptions(screen.getByLabelText("Status"), "In progress");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("heading", { name: "Tasks" })).toBeInTheDocument();
    expect(bodies).toEqual([
      {
        title: "Pay all invoices",
        description: "Before Friday",
        due_date: "2026-11-20",
        assignee: bob.id,
        status: "in_progress",
        version: 3,
      },
    ]);
  });

  it("reloads the task when someone else changed it first", async () => {
    // First read: version 3. Every read after the 409: someone else's version 4.
    server.use(
      http.get(taskUrl, () => HttpResponse.json(task), { once: true }),
      http.get(taskUrl, () => HttpResponse.json({ ...task, title: "Pay invoices today", version: 4 })),
    );
    capture("patch", taskUrl, () =>
      HttpResponse.json(
        errorBody("conflict", "Task was changed by someone else. Reload and try again."),
        { status: 409 },
      ),
    );
    const { user } = renderApp(editPath);

    await user.type(await screen.findByLabelText("Description"), " please");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Someone else changed this task. The form now shows their version; make your change again.",
    );
    expect(await screen.findByDisplayValue("Pay invoices today")).toBeInTheDocument();
  });

  it("is not offered to someone who did not create the task", async () => {
    server.use(http.get(taskUrl, () => HttpResponse.json({ ...task, created_by: bob.id })));

    renderApp(editPath);

    expect(
      await screen.findByText("Only the person who created this task can edit it."),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Title")).not.toBeInTheDocument();
  });

  it("says when the task does not exist", async () => {
    server.use(
      http.get("/api/v1/tasks/999", () =>
        HttpResponse.json(errorBody("not_found", "Task not found."), { status: 404 }),
      ),
    );

    renderApp("/tasks/999/edit");

    expect(await screen.findByRole("alert")).toHaveTextContent("Task not found.");
  });
});
