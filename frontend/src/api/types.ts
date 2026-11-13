// The only place that names generated types. Everything else imports from src/api.
import type { components, paths } from "./generated/schema";

type Schemas = components["schemas"];

export type Task = Schemas["Task"];
export type TaskStatus = Schemas["TaskStatus"];
export type User = Schemas["User"];
export type Session = Schemas["Session"];
export type ErrorBody = Schemas["Error"];
export type NewTask = Schemas["TaskCreateRequest"];
export type TaskChanges = Schemas["PatchedTaskUpdateRequest"];
export type TaskListQuery = NonNullable<paths["/api/v1/tasks"]["get"]["parameters"]["query"]>;
export type TaskPage = Schemas["PaginatedTaskList"];

export const TASK_STATUSES: readonly TaskStatus[] = ["todo", "in_progress", "done"];

export function isTaskStatus(value: unknown): value is TaskStatus {
  return TASK_STATUSES.some((status) => status === value);
}
