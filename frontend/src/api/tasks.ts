import { api, dataOf, noContent } from "./client";
import type { NewTask, Task, TaskChanges, TaskListQuery, TaskPage } from "./types";

export function listTasks(query: TaskListQuery): Promise<TaskPage> {
  return dataOf(api.GET("/api/v1/tasks", { params: { query } }));
}

export function getTask(taskId: number): Promise<Task> {
  return dataOf(api.GET("/api/v1/tasks/{task_id}", { params: { path: { task_id: taskId } } }));
}

export function createTask(task: NewTask): Promise<Task> {
  return dataOf(api.POST("/api/v1/tasks", { body: task }));
}

export function updateTask(taskId: number, changes: TaskChanges): Promise<Task> {
  return dataOf(
    api.PATCH("/api/v1/tasks/{task_id}", {
      params: { path: { task_id: taskId } },
      body: changes,
    }),
  );
}

export function deleteTask(taskId: number): Promise<void> {
  return noContent(
    api.DELETE("/api/v1/tasks/{task_id}", { params: { path: { task_id: taskId } } }),
  );
}
