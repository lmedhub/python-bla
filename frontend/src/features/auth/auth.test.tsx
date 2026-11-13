import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { alice } from "../../test/data";
import { errorBody, signedInAs, signedOut, taskListReturns, usersAre } from "../../test/handlers";
import { renderApp } from "../../test/render";
import { server } from "../../test/server";

beforeEach(() => {
  // The task list is where a signed-in user lands.
  taskListReturns([]);
  usersAre([alice]);
});

function loginAnswers(status: number, body: object, headers: Record<string, string> = {}) {
  server.use(http.post("/api/v1/auth/login", () => HttpResponse.json(body, { status, headers })));
}

describe("signing in", () => {
  it("sends a signed-out visitor to the login page", async () => {
    signedOut();

    renderApp("/tasks");

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByTestId("current-url")).toHaveTextContent("/login");
  });

  it("restores the session after a page reload", async () => {
    signedInAs(alice);

    renderApp("/tasks");

    expect(await screen.findByRole("heading", { name: "Tasks" })).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
  });

  it("signs in and goes back to the page the visitor asked for", async () => {
    signedOut();
    loginAnswers(200, { access: "access-token", user: alice });
    const { user } = renderApp("/tasks");

    await user.type(await screen.findByLabelText("Email"), "alice@example.com");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Tasks" })).toBeInTheDocument();
    expect(screen.getByTestId("current-url")).toHaveTextContent("/tasks");
  });

  it("shows the server's message for wrong credentials", async () => {
    signedOut();
    loginAnswers(401, errorBody("not_authenticated", "No active account with these credentials."));
    const { user } = renderApp("/login");

    await user.type(await screen.findByLabelText("Email"), "alice@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No active account with these credentials.",
    );
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });

  it("says how long to wait after too many attempts", async () => {
    signedOut();
    loginAnswers(429, errorBody("throttled", "Request was throttled."), { "Retry-After": "37" });
    const { user } = renderApp("/login");

    await user.type(await screen.findByLabelText("Email"), "alice@example.com");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Too many requests. Try again in 37 seconds.",
    );
  });

  it("skips the login page for someone already signed in", async () => {
    signedInAs(alice);

    renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Tasks" })).toBeInTheDocument();
  });
});

describe("signing out", () => {
  it("ends the session on the server and shows the login page", async () => {
    signedInAs(alice);
    const logout = vi.fn(() => new HttpResponse(null, { status: 204 }));
    server.use(http.post("/api/v1/auth/logout", logout));
    const { user } = renderApp("/tasks");

    await user.click(await screen.findByRole("button", { name: "Sign out" }));

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(logout).toHaveBeenCalledTimes(1);
  });
});

describe("unknown pages", () => {
  it("say so, with a way back", async () => {
    signedOut();

    renderApp("/nowhere");

    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to your tasks" })).toHaveAttribute("href", "/tasks");
  });
});
