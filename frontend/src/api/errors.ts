/** One error type for every failed API call, built from the API's single error shape. */

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

export function apiErrorFrom(_response: Response, _body: unknown): ApiError {
  throw new Error("not implemented");
}

/** A sentence for the user, whatever went wrong. */
export function userMessage(_error: unknown): string {
  throw new Error("not implemented");
}
