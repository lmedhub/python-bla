/**
 * The session, in one module (HANDOFF section 9).
 *
 * The access token lives only in this module's memory, never in storage, so a script
 * injected into the page cannot read it from there. The refresh token is an HttpOnly
 * cookie the browser sends to /api/v1/auth only.
 */
import type { Session } from "./types";

export function callerTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export function login(_email: string, _password: string): Promise<Session> {
  throw new Error("not implemented");
}

export function logout(): Promise<void> {
  throw new Error("not implemented");
}

/** One refresh at a time: every caller shares the request already in flight. */
export function refreshSession(): Promise<Session | null> {
  throw new Error("not implemented");
}

export function forgetSession(): void {
  throw new Error("not implemented");
}

/** Called when the session ends without the user asking (the refresh failed). */
export function onSessionEnded(_listener: () => void): () => void {
  throw new Error("not implemented");
}

/** fetch for the API: adds the token and time zone, refreshes once on 401, retries once. */
export function authorizedFetch(_request: Request): Promise<Response> {
  throw new Error("not implemented");
}
