import { http, HttpResponse } from "msw";
import type { User } from "../api/types";
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

/** No refresh cookie: a page load shows the login page. */
export function signedOut() {
  server.use(
    http.post("/api/v1/auth/refresh", () =>
      HttpResponse.json(errorBody("not_authenticated", "No session."), { status: 401 }),
    ),
  );
}
