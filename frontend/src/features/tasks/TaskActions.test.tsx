import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Task } from "../../api/types";
import { alice, bob, carol, makeTask } from "../../test/data";
import { errorBody, signedInAs, usersAre } from "../../test/handlers";
import { renderApp } from "../../test/render";
import { server } from "../../test/server";

/** A tiny in-memory API: the list reflects PATCH and DELETE, like the real one. */
function serveTasks(initial: Task[]) {
  let tasks = [...initial];
  const patches = vi.fn<(body: unknown) => void>();
  const deletes = vi.fn<(taskId: number) => void>();
  server.use(
    http.get("/api/v1/tasks", () =>
      HttpResponse.json({ count: tasks.length, next: null, previous: null, results: tasks }),
    ),
    http.patch("/api/v1/tasks/:taskId", async ({ params, request }) => {
      const changes = (await request.json()) as Partial<Task>;
      patches(changes);
      tasks = tasks.map((task) =>
        task.id === Number(params.taskId) ? { ...task, ...changes, version: task.version + 1 } : task,
      );
      return HttpResponse.json(tasks.find((task) => task.id === Number(params.taskId)));
    }),
    http.delete("/api/v1/tasks/:taskId", ({ params }) => {
      deletes(Number(params.taskId));
      tasks = tasks.filter((task) => task.id !== Number(params.taskId));
      return new HttpResponse(null, { status: 204 });
    }),
  );
  return { patches, deletes };
}

async function findItem(title: string) {
  const heading = await screen.findByRole("heading", { name: title });
  const item = heading.closest("li");
  if (item === null) throw new Error(`No list item for "${title}".`);
  return within(item);
}

beforeEach(() => {
  usersAre([alice, bob, carol]);
});

describe("changing the status from the list", () => {
  it("marks a task done and reopens it, without sending a version", async () => {
    signedInAs(alice);
    const { patches } = serveTasks([makeTask({ title: "Pay invoices", created_by: alice.id })]);
    const { user } = renderApp("/tasks");

    await user.click((await findItem("Pay invoices")).getByRole("button", { name: "Mark done" }));

    const item = await findItem("Pay invoices");
    expect(await item.findByText("Done")).toBeInTheDocument();
    await user.click(item.getByRole("button", { name: "Reopen" }));
    expect(await item.findByText("To do")).toBeInTheDocument();
    // A quick toggle should not fail just because someone edited the description.
    expect(patches.mock.calls).toEqual([[{ status: "done" }], [{ status: "todo" }]]);
  });

  it("shows why a change was refused", async () => {
    signedInAs(alice);
    server.use(
      http.get("/api/v1/tasks", () =>
        HttpResponse.json({
          count: 1,
          next: null,
          previous: null,
          results: [makeTask({ title: "Pay invoices", created_by: alice.id })],
        }),
      ),
      http.patch("/api/v1/tasks/:taskId", () =>
        HttpResponse.json(errorBody("permission_denied", "You may not change this task."), {
          status: 403,
        }),
      ),
    );
    const { user } = renderApp("/tasks");

    await user.click((await findItem("Pay invoices")).getByRole("button", { name: "Mark done" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("You may not change this task.");
  });
});

describe("what each person may do", () => {
  const task = makeTask({ title: "Pay invoices", created_by: alice.id, assignee: bob.id });

  it("lets the creator edit, delete and change the status", async () => {
    signedInAs(alice);
    serveTasks([task]);
    renderApp("/tasks");

    const item = await findItem("Pay invoices");
    expect(item.getByRole("link", { name: "Edit" })).toHaveAttribute(
      "href",
      `/tasks/${String(task.id)}/edit`,
    );
    expect(item.getByRole("button", { name: "Delete" })).toBeEnabled();
    expect(item.getByRole("button", { name: "Mark done" })).toBeEnabled();
  });

  it("lets the assignee change the status only", async () => {
    signedInAs(bob);
    serveTasks([task]);
    renderApp("/tasks");

    const item = await findItem("Pay invoices");
    expect(item.getByRole("button", { name: "Mark done" })).toBeEnabled();
    expect(item.getByRole("button", { name: "Edit" })).toBeDisabled();
    expect(item.getByRole("button", { name: "Delete" })).toBeDisabled();
  });

  it("lets everyone else only read", async () => {
    signedInAs(carol);
    serveTasks([task]);
    renderApp("/tasks");

    const item = await findItem("Pay invoices");
    expect(item.getByRole("button", { name: "Mark done" })).toBeDisabled();
    expect(item.getByRole("button", { name: "Edit" })).toBeDisabled();
    expect(item.getByRole("button", { name: "Delete" })).toBeDisabled();
  });
});

describe("deleting a task", () => {
  it("asks first, and cancelling deletes nothing", async () => {
    signedInAs(alice);
    const { deletes } = serveTasks([makeTask({ title: "Pay invoices", created_by: alice.id })]);
    const { user } = renderApp("/tasks");

    await user.click((await findItem("Pay invoices")).getByRole("button", { name: "Delete" }));

    const dialog = screen.getByRole("dialog", { name: 'Delete "Pay invoices"?' });
    // The safe choice has the focus, so Enter does not delete by accident.
    expect(within(dialog).getByRole("button", { name: "Cancel" })).toHaveFocus();
    await user.click(within(dialog).getByRole("button", { name: "Cancel" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(deletes).not.toHaveBeenCalled();
    expect(screen.getByRole("heading", { name: "Pay invoices" })).toBeInTheDocument();
  });

  it("removes the task once confirmed", async () => {
    signedInAs(alice);
    const task = makeTask({ title: "Pay invoices", created_by: alice.id });
    const { deletes } = serveTasks([task]);
    const { user } = renderApp("/tasks");

    await user.click((await findItem("Pay invoices")).getByRole("button", { name: "Delete" }));
    await user.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Delete task" }),
    );

    expect(await screen.findByText("No tasks yet.")).toBeInTheDocument();
    expect(deletes).toHaveBeenCalledWith(task.id);
  });

  it("keeps the dialog open with the reason when the delete fails", async () => {
    signedInAs(alice);
    serveTasks([makeTask({ title: "Pay invoices", created_by: alice.id })]);
    server.use(
      http.delete("/api/v1/tasks/:taskId", () =>
        HttpResponse.json(errorBody("permission_denied", "Only the creator may delete this task."), {
          status: 403,
        }),
      ),
    );
    const { user } = renderApp("/tasks");

    await user.click((await findItem("Pay invoices")).getByRole("button", { name: "Delete" }));
    await user.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Delete task" }),
    );

    expect(await within(screen.getByRole("dialog")).findByRole("alert")).toHaveTextContent(
      "Only the creator may delete this task.",
    );
  });
});
