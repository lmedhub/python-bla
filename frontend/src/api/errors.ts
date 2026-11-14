/** One error type for every failed API call, built from the API's single error shape. */

import type { ErrorBody } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  /** Field name to messages, for showing errors next to form inputs. */
  readonly fields: Readonly<Record<string, string[]>>;
  /** Seconds from the Retry-After header of a 429, when the server sent one. */
  readonly retryAfterSeconds: number | null;

  constructor(options: {
    status: number;
    code: string;
    detail: string;
    fields?: Record<string, string[]>;
    retryAfterSeconds?: number | null;
  }) {
    super(options.detail);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.fields = options.fields ?? {};
    this.retryAfterSeconds = options.retryAfterSeconds ?? null;
  }
}

export function apiErrorFrom(response: Response, body: unknown): ApiError {
  const retryAfter = Number.parseInt(response.headers.get("Retry-After") ?? "", 10);
  const retryAfterSeconds = Number.isNaN(retryAfter) ? null : retryAfter;
  if (isErrorBody(body)) {
    return new ApiError({ status: response.status, ...body, retryAfterSeconds });
  }
  // Not our API's shape, e.g. an HTML error page from a proxy.
  return new ApiError({
    status: response.status,
    code: "error",
    detail: `The server answered with an error (${String(response.status)}).`,
    retryAfterSeconds,
  });
}

/** A sentence for the user, whatever went wrong. */
export function userMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "throttled" && error.retryAfterSeconds !== null) {
      return `Too many requests. Try again in ${String(error.retryAfterSeconds)} seconds.`;
    }
    return error.message;
  }
  // fetch rejects with a TypeError when the network or the server is unreachable.
  if (error instanceof TypeError) {
    return "Cannot reach the server. Check your connection and try again.";
  }
  return "Something went wrong. Please try again.";
}

function isErrorBody(body: unknown): body is ErrorBody {
  return (
    typeof body === "object" &&
    body !== null &&
    "code" in body &&
    typeof body.code === "string" &&
    "detail" in body &&
    typeof body.detail === "string" &&
    "fields" in body &&
    typeof body.fields === "object"
  );
}
