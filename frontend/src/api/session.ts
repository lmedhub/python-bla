/**
 * The session, in one module (HANDOFF section 9).
 *
 * The access token lives only in this module's memory, never in storage, so a script
 * injected into the page cannot read it from there. The refresh token is an HttpOnly
 * cookie the browser sends to /api/v1/auth only.
 */
import createClient from "openapi-fetch";
import { apiErrorFrom } from "./errors";
import type { paths } from "./generated/schema";
import type { Session } from "./types";

let accessToken: string | null = null;
let refreshInFlight: Promise<Session | null> | null = null;
const sessionEndedListeners = new Set<() => void>();

// Login, refresh and logout must never trigger the refresh-and-retry logic themselves.
const authApi = createClient<paths>({
  baseUrl: window.location.origin,
  fetch: (request) => fetch(withTimeZone(request)),
});

export function callerTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export async function login(email: string, password: string): Promise<Session> {
  const { data, error, response } = await authApi.POST("/api/v1/auth/login", {
    body: { email, password },
  });
  if (!data) {
    throw apiErrorFrom(response, error);
  }
  accessToken = data.access;
  return data;
}

export async function logout(): Promise<void> {
  forgetSession();
  try {
    await authApi.POST("/api/v1/auth/logout");
  } catch {
    // Signed out here either way. The server-side refresh token then simply expires.
  }
}

/** One refresh at a time: every caller shares the request already in flight. */
export function refreshSession(): Promise<Session | null> {
  refreshInFlight ??= requestRefresh().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

async function requestRefresh(): Promise<Session | null> {
  const { data } = await authApi.POST("/api/v1/auth/refresh");
  accessToken = data?.access ?? null;
  return data ?? null;
}

export function forgetSession(): void {
  accessToken = null;
}

/** Called when the session ends without the user asking (the refresh failed). */
export function onSessionEnded(listener: () => void): () => void {
  sessionEndedListeners.add(listener);
  return () => {
    sessionEndedListeners.delete(listener);
  };
}

/** fetch for the API: adds the token and time zone, refreshes once on 401, retries once. */
export async function authorizedFetch(request: Request): Promise<Response> {
  // A request body can be read only once, so keep a copy for the retry.
  const retry = request.clone();
  const response = await fetch(withAuthorization(withTimeZone(request)));
  if (response.status !== 401) {
    return response;
  }
  const session = await refreshSession();
  if (session === null) {
    for (const listener of sessionEndedListeners) {
      listener();
    }
    return response;
  }
  return fetch(withAuthorization(withTimeZone(retry)));
}

function withTimeZone(request: Request): Request {
  // The API decides "today" and "overdue" in the caller's zone (ADR 0007).
  request.headers.set("X-Timezone", callerTimeZone());
  return request;
}

function withAuthorization(request: Request): Request {
  if (accessToken !== null) {
    request.headers.set("Authorization", `Bearer ${accessToken}`);
  }
  return request;
}
