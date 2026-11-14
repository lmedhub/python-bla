import { api, dataOf } from "./client";
import type { User } from "./types";

export function listUsers(): Promise<User[]> {
  return dataOf(api.GET("/api/v1/users"));
}
