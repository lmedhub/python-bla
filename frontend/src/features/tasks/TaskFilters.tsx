import { isTaskStatus, TASK_STATUSES, type User } from "../../api/types";
import type { TaskFilters as Filters } from "./filters";
import { STATUS_LABELS } from "./status";
import styles from "./TaskFilters.module.css";

interface TaskFiltersProps {
  filters: Filters;
  users: User[] | undefined;
  /** Called with the changed filters only. */
  onChange: (changes: Partial<Filters>) => void;
  onClear: () => void;
}

/** Each control applies at once: the URL, and so the list, follows every change. */
export function TaskFilters({ filters, users, onChange, onClear }: TaskFiltersProps) {
  return (
    <form
      className={styles.filters}
      aria-label="Filters"
      onSubmit={(event) => {
        event.preventDefault();
      }}
    >
      <div className={styles.field}>
        <label htmlFor="filter-status">Status</label>
        <select
          id="filter-status"
          value={filters.status ?? ""}
          onChange={(event) => {
            const { value } = event.target;
            onChange({ status: isTaskStatus(value) ? value : undefined });
          }}
        >
          <option value="">Any status</option>
          {TASK_STATUSES.map((status) => (
            <option key={status} value={status}>
              {STATUS_LABELS[status]}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.field}>
        <label htmlFor="filter-assignee">Assignee</label>
        <select
          id="filter-assignee"
          value={filters.assignee ?? ""}
          onChange={(event) => {
            onChange({ assignee: event.target.value || undefined });
          }}
        >
          <option value="">Anyone</option>
          <option value="me">Me</option>
          {users?.map((user) => (
            <option key={user.id} value={String(user.id)}>
              {user.name}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.field}>
        <label htmlFor="filter-due-after">Due after</label>
        <input
          id="filter-due-after"
          type="date"
          value={filters.dueAfter ?? ""}
          onChange={(event) => {
            onChange({ dueAfter: event.target.value || undefined });
          }}
        />
      </div>

      <div className={styles.field}>
        <label htmlFor="filter-due-before">Due before</label>
        <input
          id="filter-due-before"
          type="date"
          value={filters.dueBefore ?? ""}
          onChange={(event) => {
            onChange({ dueBefore: event.target.value || undefined });
          }}
        />
      </div>

      <div className={styles.field}>
        <label htmlFor="filter-overdue">Overdue</label>
        <select
          id="filter-overdue"
          value={filters.overdue === undefined ? "" : String(filters.overdue)}
          onChange={(event) => {
            const { value } = event.target;
            onChange({ overdue: value === "" ? undefined : value === "true" });
          }}
        >
          <option value="">Any</option>
          <option value="true">Overdue only</option>
          <option value="false">Not overdue</option>
        </select>
      </div>

      <button type="button" className={["secondary", styles.clear].join(" ")} onClick={onClear}>
        Clear filters
      </button>
    </form>
  );
}
