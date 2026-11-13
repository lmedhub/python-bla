import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { listTasks } from "../../api/tasks";
import type { User } from "../../api/types";
import { listUsers } from "../../api/users";
import { queryFromFilters, type TaskFilters } from "./filters";

// Every task query starts with "tasks", so one invalidation refreshes lists and details.
export const taskKeys = {
  all: ["tasks"] as const,
  list: (filters: TaskFilters) => ["tasks", "list", filters] as const,
  detail: (taskId: number) => ["tasks", "detail", taskId] as const,
};

export function useTaskPage(filters: TaskFilters) {
  return useQuery({
    queryKey: taskKeys.list(filters),
    queryFn: () => listTasks(queryFromFilters(filters)),
    // Keep showing the current page while the next one loads, instead of a blank list.
    placeholderData: keepPreviousData,
  });
}

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: listUsers,
    // The team changes rarely; no need to ask on every page.
    staleTime: 5 * 60 * 1000,
  });
}

/** A user's name for display. /users lists active users only. */
export function userName(users: User[] | undefined, userId: number): string {
  if (users === undefined) return "…";
  return users.find((user) => user.id === userId)?.name ?? "Inactive user";
}
