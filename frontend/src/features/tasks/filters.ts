import type { TaskListQuery, TaskStatus } from "../../api/types";

/** The list's filters and page. They live in the URL, so reload and share keep them. */
export interface TaskFilters {
  status?: TaskStatus;
  /** A user id, or "me". */
  assignee?: string;
  dueAfter?: string;
  dueBefore?: string;
  overdue?: boolean;
  page: number;
}

export const PAGE_SIZE = 10;

export function filtersFromSearch(_search: URLSearchParams): TaskFilters {
  throw new Error("not implemented");
}

export function searchFromFilters(_filters: TaskFilters): URLSearchParams {
  throw new Error("not implemented");
}

export function queryFromFilters(_filters: TaskFilters): TaskListQuery {
  throw new Error("not implemented");
}
