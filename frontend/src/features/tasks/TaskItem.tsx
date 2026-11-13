import { useId, useState } from "react";
import { Link } from "react-router";
import { userMessage } from "../../api/errors";
import type { Task, User } from "../../api/types";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { formatDate } from "../../lib/dates";
import { useCurrentUser } from "../auth/AuthProvider";
import { canChangeStatus, canDelete, canEdit } from "./permissions";
import { useDeleteTask, useUpdateTask, userName } from "./queries";
import { STATUS_LABELS } from "./status";
import styles from "./TaskItem.module.css";

interface TaskItemProps {
  task: Task;
  users: User[] | undefined;
}

export function TaskItem({ task, users }: TaskItemProps) {
  const currentUser = useCurrentUser();
  const update = useUpdateTask();
  const remove = useDeleteTask();
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  // Buttons say "Edit", "Delete"; the description tells a screen reader which task.
  const titleId = useId();
  const done = task.status === "done";

  return (
    <li className={styles.item}>
      <div className={styles.heading}>
        <h2 id={titleId} className={styles.title}>
          {task.title}
        </h2>
        {task.is_overdue && <span className={styles.overdue}>Overdue</span>}
      </div>
      <dl className={styles.details}>
        <div>
          <dt>Status</dt>
          <dd>{STATUS_LABELS[task.status]}</dd>
        </div>
        <div>
          <dt>Due</dt>
          <dd>{task.due_date ? formatDate(task.due_date) : "No due date"}</dd>
        </div>
        <div>
          <dt>Assignee</dt>
          <dd>{task.assignee === null ? "Unassigned" : userName(users, task.assignee)}</dd>
        </div>
        <div>
          <dt>Created by</dt>
          <dd>{userName(users, task.created_by)}</dd>
        </div>
      </dl>

      {/* Actions the user may not take are disabled; the API enforces the same rules. */}
      <div className={styles.actions}>
        <button
          type="button"
          className="secondary"
          aria-describedby={titleId}
          disabled={!canChangeStatus(task, currentUser.id) || update.isPending}
          onClick={() => {
            // No version: a status toggle should not fail because someone fixed a typo.
            update.mutate({ taskId: task.id, changes: { status: done ? "todo" : "done" } });
          }}
        >
          {done ? "Reopen" : "Mark done"}
        </button>
        {canEdit(task, currentUser.id) ? (
          <Link
            to={`/tasks/${String(task.id)}/edit`}
            className="button secondary"
            aria-describedby={titleId}
          >
            Edit
          </Link>
        ) : (
          <button type="button" className="secondary" disabled aria-describedby={titleId}>
            Edit
          </button>
        )}
        <button
          type="button"
          className="secondary"
          aria-describedby={titleId}
          disabled={!canDelete(task, currentUser.id)}
          onClick={() => {
            setConfirmingDelete(true);
          }}
        >
          Delete
        </button>
      </div>
      {update.isError && (
        <p role="alert" className={styles.error}>
          {userMessage(update.error)}
        </p>
      )}

      {confirmingDelete && (
        <ConfirmDialog
          title={`Delete "${task.title}"?`}
          message="This cannot be undone."
          confirmLabel="Delete task"
          pending={remove.isPending}
          error={remove.error}
          onConfirm={() => {
            remove.mutate(task.id);
          }}
          onCancel={() => {
            setConfirmingDelete(false);
            remove.reset();
          }}
        />
      )}
    </li>
  );
}
