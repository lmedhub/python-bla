import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { alice } from "../test/data";
import { server } from "../test/server";
import { ApiError } from "./errors";
import { forgetSession, login, logout, onSessionEnded, refreshSession } from "./session";
import { listUsers } from "./users";

const USERS = "/api/v1/users";
const REFRESH = "/api/v1/auth/refresh";

function signInAs(access: string) {
  server.use(http.post("/api/v1/auth/login", () => HttpResponse.json({ access, user: alice })));
  return login("alice@example.com", "secret");
}

/** /users answers only to the given token, like the real API with an expired one. */
function usersAcceptOnly(token: string) {
  server.use(
    http.get(USERS, ({ request }) =>
      request.headers.get("Authorization") === `Bearer ${token}`
        ? HttpResponse.json([alice])
        : HttpResponse.json(
            { code: "not_authenticated", detail: "Token expired.", fields: {} },
            { status: 401 },
          ),
    ),
  );
}

beforeEach(() => {
  forgetSession();
});

describe("login", () => {
  it("keeps the access token and sends it with the caller's time zone", async () => {
    let headers = new Headers();
    server.use(
      http.get(USERS, ({ request }) => {
        headers = request.headers;
        return HttpResponse.json([alice]);
      }),
    );

    const session = await signInAs("token-1");
    await listUsers();

    expect(session.user).toEqual(alice);
    expect(headers.get("Authorization")).toBe("Bearer token-1");
    // vite.config.ts runs the tests in this zone.
    expect(headers.get("X-Timezone")).toBe("America/Sao_Paulo");
  });

  it("rejects with the server's message on bad credentials", async () => {
    server.use(
      http.post("/api/v1/auth/login", () =>
        HttpResponse.json(
          { code: "not_authenticated", detail: "Wrong email or password.", fields: {} },
          { status: 401 },
        ),
      ),
    );

    await expect(login("alice@example.com", "wrong")).rejects.toThrow("Wrong email or password.");
  });
});

describe("an expired access token", () => {
  it("is refreshed once and the request retried", async () => {
    await signInAs("expired");
    usersAcceptOnly("fresh");
    const refresh = vi.fn(() => HttpResponse.json({ access: "fresh", user: alice }));
    server.use(http.post(REFRESH, refresh));

    await expect(listUsers()).resolves.toEqual([alice]);
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("is refreshed only once for requests that fail together", async () => {
    // Refresh tokens rotate and are blacklisted after use: a second parallel refresh
    // would present a used token and sign the user out.
    await signInAs("expired");
    usersAcceptOnly("fresh");
    const refresh = vi.fn(() => HttpResponse.json({ access: "fresh", user: alice }));
    server.use(http.post(REFRESH, refresh));

    await Promise.all([listUsers(), listUsers(), listUsers()]);

    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("ends the session when the refresh fails too", async () => {
    await signInAs("expired");
    usersAcceptOnly("fresh");
    server.use(
      http.post(REFRESH, () =>
        HttpResponse.json(
          { code: "not_authenticated", detail: "Session expired.", fields: {} },
          { status: 401 },
        ),
      ),
    );
    const ended = vi.fn();
    const unsubscribe = onSessionEnded(ended);

    await expect(listUsers()).rejects.toBeInstanceOf(ApiError);
    expect(ended).toHaveBeenCalledTimes(1);
    unsubscribe();
  });
});

describe("refreshSession", () => {
  it("restores the session from the cookie after a page reload", async () => {
    server.use(http.post(REFRESH, () => HttpResponse.json({ access: "restored", user: alice })));
    usersAcceptOnly("restored");

    const session = await refreshSession();

    expect(session?.user).toEqual(alice);
    await expect(listUsers()).resolves.toEqual([alice]);
  });

  it("returns null when there is no valid cookie", async () => {
    server.use(
      http.post(REFRESH, () =>
        HttpResponse.json(
          { code: "not_authenticated", detail: "No session.", fields: {} },
          { status: 401 },
        ),
      ),
    );

    await expect(refreshSession()).resolves.toBeNull();
  });
});

describe("logout", () => {
  it("forgets the token even if the server call fails", async () => {
    await signInAs("token-1");
    server.use(http.post("/api/v1/auth/logout", () => HttpResponse.error()));
    let authorization: string | null = "unset";
    server.use(
      http.get(USERS, ({ request }) => {
        authorization = request.headers.get("Authorization");
        return HttpResponse.json(
          { code: "not_authenticated", detail: "No token.", fields: {} },
          { status: 401 },
        );
      }),
      http.post(REFRESH, () =>
        HttpResponse.json(
          { code: "not_authenticated", detail: "No session.", fields: {} },
          { status: 401 },
        ),
      ),
    );

    await logout();

    await expect(listUsers()).rejects.toBeInstanceOf(ApiError);
    expect(authorization).toBeNull();
  });
});
