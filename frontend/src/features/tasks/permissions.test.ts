import { describe, expect, it } from "vitest";
import { alice, bob, carol, makeTask } from "../../test/data";
import { canChangeStatus, canDelete, canEdit } from "./permissions";

const task = makeTask({ created_by: alice.id, assignee: bob.id });

describe("task permissions", () => {
  it("lets the creator do everything", () => {
    expect(canEdit(task, alice.id)).toBe(true);
    expect(canChangeStatus(task, alice.id)).toBe(true);
    expect(canDelete(task, alice.id)).toBe(true);
  });

  it("lets the assignee change the status only", () => {
    expect(canEdit(task, bob.id)).toBe(false);
    expect(canChangeStatus(task, bob.id)).toBe(true);
    expect(canDelete(task, bob.id)).toBe(false);
  });

  it("lets everyone else only read", () => {
    expect(canEdit(task, carol.id)).toBe(false);
    expect(canChangeStatus(task, carol.id)).toBe(false);
    expect(canDelete(task, carol.id)).toBe(false);
  });

  it("does not treat an unassigned task as assigned to anyone", () => {
    expect(canChangeStatus(makeTask({ created_by: alice.id, assignee: null }), bob.id)).toBe(false);
  });
});
