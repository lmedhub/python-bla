import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createTask, deleteTask, getTask, listTasks, updateTask } from "../../api/tasks";
import type { TaskChanges, User } from "../../api/types";
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

export function useTask(taskId: number) {
  return useQuery({ queryKey: taskKeys.detail(taskId), queryFn: () => getTask(taskId) });
}

/** After any change, every task query is stale: lists and details alike. */
function useInvalidateTasks() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: taskKeys.all });
}

export function useCreateTask() {
  const invalidate = useInvalidateTasks();
  return useMutation({ mutationFn: createTask, onSuccess: invalidate });
}

export function useUpdateTask() {
  const invalidate = useInvalidateTasks();
  return useMutation({
    mutationFn: ({ taskId, changes }: { taskId: number; changes: TaskChanges }) =>
      updateTask(taskId, changes),
    onSuccess: invalidate,
  });
}

export function useDeleteTask() {
  const invalidate = useInvalidateTasks();
  return useMutation({ mutationFn: deleteTask, onSuccess: invalidate });
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
