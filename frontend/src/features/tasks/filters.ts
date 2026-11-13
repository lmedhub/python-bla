import { isTaskStatus, type TaskListQuery, type TaskStatus } from "../../api/types";

/**
 * The list's filters and page. They live in the URL, so reload and share keep them.
 * `undefined` means "not filtered"; it is allowed explicitly so a filter can be cleared.
 */
export interface TaskFilters {
  status?: TaskStatus | undefined;
  /** A user id, or "me". */
  assignee?: string | undefined;
  dueAfter?: string | undefined;
  dueBefore?: string | undefined;
  overdue?: boolean | undefined;
  page: number;
}

export function hasFilters(filters: TaskFilters): boolean {
  return [filters.status, filters.assignee, filters.dueAfter, filters.dueBefore, filters.overdue].some(
    (value) => value !== undefined,
  );
}

export const PAGE_SIZE = 10;

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const ASSIGNEE = /^(me|\d+)$/;

/** Reads the URL. Values a hand-edited URL could contain are ignored, not sent to the API. */
export function filtersFromSearch(search: URLSearchParams): TaskFilters {
  const filters: TaskFilters = { page: 1 };
  const status = search.get("status");
  if (isTaskStatus(status)) {
    filters.status = status;
  }
  const assignee = search.get("assignee");
  if (assignee !== null && ASSIGNEE.test(assignee)) {
    filters.assignee = assignee;
  }
  const dueAfter = search.get("due_after");
  if (dueAfter !== null && ISO_DATE.test(dueAfter)) {
    filters.dueAfter = dueAfter;
  }
  const dueBefore = search.get("due_before");
  if (dueBefore !== null && ISO_DATE.test(dueBefore)) {
    filters.dueBefore = dueBefore;
  }
  const overdue = search.get("overdue");
  if (overdue === "true" || overdue === "false") {
    filters.overdue = overdue === "true";
  }
  const page = Number(search.get("page"));
  if (Number.isInteger(page) && page > 1) {
    filters.page = page;
  }
  return filters;
}

/** Writes the URL. Only what is set, so a plain list has a plain URL. */
export function searchFromFilters(filters: TaskFilters): URLSearchParams {
  const search = new URLSearchParams();
  if (filters.status) search.set("status", filters.status);
  if (filters.assignee) search.set("assignee", filters.assignee);
  if (filters.dueAfter) search.set("due_after", filters.dueAfter);
  if (filters.dueBefore) search.set("due_before", filters.dueBefore);
  if (filters.overdue !== undefined) search.set("overdue", String(filters.overdue));
  if (filters.page > 1) search.set("page", String(filters.page));
  return search;
}

export function queryFromFilters(filters: TaskFilters): TaskListQuery {
  const query: TaskListQuery = { page: filters.page, page_size: PAGE_SIZE };
  if (filters.status) query.status = filters.status;
  if (filters.assignee) query.assignee = filters.assignee;
  if (filters.dueAfter) query.due_after = filters.dueAfter;
  if (filters.dueBefore) query.due_before = filters.dueBefore;
  if (filters.overdue !== undefined) query.overdue = filters.overdue;
  return query;
}
