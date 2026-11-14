import type { Task, User } from "../api/types";

export const alice: User = { id: 1, email: "alice@example.com", name: "Alice" };
export const bob: User = { id: 2, email: "bob@example.com", name: "Bob" };
export const carol: User = { id: 3, email: "carol@example.com", name: "Carol" };

let nextId = 100;

export function makeTask(fields: Partial<Task> = {}): Task {
  nextId += 1;
  return {
    id: nextId,
    title: `Task ${String(nextId)}`,
    description: "",
    status: "todo",
    due_date: null,
    created_by: alice.id,
    assignee: null,
    completed_at: null,
    created_at: "2026-11-01T09:00:00Z",
    updated_at: "2026-11-01T09:00:00Z",
    version: 1,
    is_overdue: false,
    ...fields,
  };
}
