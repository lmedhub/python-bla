import { describe, expect, it } from "vitest";
import { formatDate, formatDateTime, todayIso } from "./dates";

// The test run uses TZ=America/Sao_Paulo (UTC-3), see vite.config.ts.
describe("formatDate", () => {
  it("shows a due date on its own calendar day, even west of UTC", () => {
    // new Date("2026-11-12") is UTC midnight, which is 11 Nov at 21:00 in Sao Paulo.
    expect(formatDate("2026-11-12", "en-US")).toBe("Nov 12, 2026");
  });
});

describe("formatDateTime", () => {
  it("shows an instant in the local time zone", () => {
    expect(formatDateTime("2026-11-13T01:30:00Z", "en-US")).toMatch(/^Nov 12, 2026, 10:30\sPM$/);
  });
});

describe("todayIso", () => {
  it("is the local calendar date, not the UTC one", () => {
    expect(todayIso(new Date("2026-11-13T01:30:00Z"))).toBe("2026-11-12");
  });

  it("pads month and day", () => {
    expect(todayIso(new Date(2026, 0, 5, 12))).toBe("2026-01-05");
  });
});
