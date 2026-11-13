import { describe, expect, it } from "vitest";
import { ApiError, apiErrorFrom, userMessage } from "./errors";

function response(status: number, headers: Record<string, string> = {}): Response {
  return new Response(null, { status, headers });
}

describe("apiErrorFrom", () => {
  it("reads the API's error shape", () => {
    const error = apiErrorFrom(response(400), {
      code: "invalid_input",
      detail: "Invalid input.",
      fields: { title: ["This field may not be blank."] },
    });

    expect(error.status).toBe(400);
    expect(error.code).toBe("invalid_input");
    expect(error.message).toBe("Invalid input.");
    expect(error.fields).toEqual({ title: ["This field may not be blank."] });
  });

  it("reads Retry-After on a 429", () => {
    const error = apiErrorFrom(response(429, { "Retry-After": "42" }), {
      code: "throttled",
      detail: "Request was throttled.",
      fields: {},
    });

    expect(error.retryAfterSeconds).toBe(42);
  });

  it("copes with a body that is not the API's shape (a proxy's HTML error page)", () => {
    const error = apiErrorFrom(response(502), "<html>Bad Gateway</html>");

    expect(error.code).toBe("error");
    expect(error.message).toBe("The server answered with an error (502).");
    expect(error.fields).toEqual({});
  });
});

describe("userMessage", () => {
  it("uses the server's sentence", () => {
    const error = new ApiError({ status: 403, code: "permission_denied", detail: "Not allowed." });

    expect(userMessage(error)).toBe("Not allowed.");
  });

  it("says how long to wait when rate limited", () => {
    const error = new ApiError({
      status: 429,
      code: "throttled",
      detail: "Request was throttled.",
      retryAfterSeconds: 42,
    });

    expect(userMessage(error)).toBe("Too many requests. Try again in 42 seconds.");
  });

  it("explains a network failure", () => {
    expect(userMessage(new TypeError("Failed to fetch"))).toBe(
      "Cannot reach the server. Check your connection and try again.",
    );
  });

  it("has a fallback for anything else", () => {
    expect(userMessage(new Error("boom"))).toBe("Something went wrong. Please try again.");
  });
});
