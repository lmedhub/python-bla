import { http, HttpResponse } from "msw";
import type { Task, User } from "../api/types";
import { alice } from "./data";
import { server } from "./server";

export function errorBody(code: string, detail: string, fields: Record<string, string[]> = {}) {
  return { code, detail, fields };
}

/** A valid refresh cookie: a page load restores the session as `user`. */
export function signedInAs(user: User = alice) {
  server.use(
    http.post("/api/v1/auth/refresh", () => HttpResponse.json({ access: "access-token", user })),
  );
}

/** No refresh cookie: the API answers 204, and a page load shows the login page. */
export function signedOut() {
  server.use(http.post("/api/v1/auth/refresh", () => new HttpResponse(null, { status: 204 })));
}

/** GET /tasks answers with `tasks` (and `count`, for paging); returns the URLs requested. */
export function taskListReturns(tasks: Task[], count = tasks.length): URL[] {
  const requested: URL[] = [];
  server.use(
    http.get("/api/v1/tasks", ({ request }) => {
      requested.push(new URL(request.url));
      return HttpResponse.json({ count, next: null, previous: null, results: tasks });
    }),
  );
  return requested;
}

export function usersAre(users: User[]) {
  server.use(http.get("/api/v1/users", () => HttpResponse.json(users)));
}
