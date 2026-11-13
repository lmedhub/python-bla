import { describe, expect, it } from "vitest";
import { filtersFromSearch, queryFromFilters, searchFromFilters } from "./filters";

describe("filtersFromSearch", () => {
  it("reads every filter from the URL", () => {
    const search = new URLSearchParams(
      "status=in_progress&assignee=me&due_after=2026-11-01&due_before=2026-11-30&overdue=true&page=3",
    );

    expect(filtersFromSearch(search)).toEqual({
      status: "in_progress",
      assignee: "me",
      dueAfter: "2026-11-01",
      dueBefore: "2026-11-30",
      overdue: true,
      page: 3,
    });
  });

  it("starts on page 1 with no filters", () => {
    expect(filtersFromSearch(new URLSearchParams())).toEqual({ page: 1 });
  });

  it("ignores values a hand-edited URL could contain", () => {
    const search = new URLSearchParams(
      "status=urgent&assignee=bob&due_after=tomorrow&overdue=yes&page=-2",
    );

    expect(filtersFromSearch(search)).toEqual({ page: 1 });
  });

  it("reads overdue=false as a real filter", () => {
    expect(filtersFromSearch(new URLSearchParams("overdue=false"))).toEqual({
      overdue: false,
      page: 1,
    });
  });
});

describe("searchFromFilters", () => {
  it("writes only what is set, and leaves page 1 out", () => {
    expect(searchFromFilters({ status: "done", assignee: "2", page: 1 }).toString()).toBe(
      "status=done&assignee=2",
    );
  });

  it("round-trips through the URL", () => {
    const filters = {
      status: "todo" as const,
      assignee: "me",
      dueAfter: "2026-11-01",
      dueBefore: "2026-11-30",
      overdue: false,
      page: 2,
    };

    expect(filtersFromSearch(searchFromFilters(filters))).toEqual(filters);
  });
});

describe("queryFromFilters", () => {
  it("maps the filters to the API's query parameters", () => {
    expect(queryFromFilters({ status: "todo", dueAfter: "2026-11-01", overdue: true, page: 2 })).toEqual(
      { status: "todo", due_after: "2026-11-01", overdue: true, page: 2, page_size: 10 },
    );
  });
});
