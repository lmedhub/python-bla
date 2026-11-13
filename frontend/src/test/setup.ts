import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, beforeEach, expect, vi } from "vitest";
import { server } from "./server";

// jsdom does not implement <dialog>'s modal methods. The browser provides the real behavior
// (focus trap, Esc to close), checked by hand; tests only need open/closed.
HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
  this.open = true;
};
HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
  this.open = false;
  this.dispatchEvent(new Event("close"));
};

beforeAll(() => {
  // A request no test expected is a bug in the test or the code, never a silent pass.
  server.listen({ onUnhandledFrame: "error" });
});

beforeEach(() => {
  vi.spyOn(console, "error");
  vi.spyOn(console, "warn");
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
  // HANDOFF: no console warnings or errors. React reports act() and key problems here.
  expect(console.error).not.toHaveBeenCalled();
  expect(console.warn).not.toHaveBeenCalled();
  vi.restoreAllMocks();
});

afterAll(() => {
  server.close();
});
