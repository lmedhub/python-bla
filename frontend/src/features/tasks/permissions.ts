import type { Task } from "../../api/types";

// Mirrors the API's rules (HANDOFF section 4) to disable what the user may not do.
// The API still enforces them; this only keeps the UI honest.

export function canEdit(task: Task, userId: number): boolean {
  return task.created_by === userId;
}

export function canChangeStatus(task: Task, userId: number): boolean {
  return task.created_by === userId || task.assignee === userId;
}

export function canDelete(task: Task, userId: number): boolean {
  return task.created_by === userId;
}
