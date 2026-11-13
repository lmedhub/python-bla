import createClient from "openapi-fetch";
import { apiErrorFrom } from "./errors";
import type { paths } from "./generated/schema";
import { authorizedFetch } from "./session";

// Absolute, because fetch outside a browser (the tests) needs a full URL. In the browser
// this is the page's own origin, so requests stay same-origin behind the proxy.
export const API_ORIGIN = window.location.origin;

export const api = createClient<paths>({ baseUrl: API_ORIGIN, fetch: authorizedFetch });

interface Result<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

/** The data of a successful call, or an ApiError. */
export async function dataOf<T>(call: Promise<Result<T>>): Promise<T> {
  const { data, error, response } = await call;
  if (!response.ok || data === undefined) {
    throw apiErrorFrom(response, error);
  }
  return data;
}

/** For calls that answer 204 No Content. */
export async function noContent(call: Promise<Result<unknown>>): Promise<void> {
  const { error, response } = await call;
  if (!response.ok) {
    throw apiErrorFrom(response, error);
  }
}
