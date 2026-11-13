import type { Task } from "../../api/types";

// Mirrors the API's rules (HANDOFF section 4) to disable what the user may not do.
// The API still enforces them; this only keeps the UI honest.

export function canEdit(_task: Task, _userId: number): boolean {
  throw new Error("not implemented");
}

export function canChangeStatus(_task: Task, _userId: number): boolean {
  throw new Error("not implemented");
}

export function canDelete(_task: Task, _userId: number): boolean {
  throw new Error("not implemented");
}
