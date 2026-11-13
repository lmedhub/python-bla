import type { Task, User } from "../../api/types";
import { formatDate } from "../../lib/dates";
import { userName } from "./queries";
import { STATUS_LABELS } from "./status";
import styles from "./TaskItem.module.css";

interface TaskItemProps {
  task: Task;
  users: User[] | undefined;
}

export function TaskItem({ task, users }: TaskItemProps) {
  return (
    <li className={styles.item}>
      <div className={styles.heading}>
        <h2 className={styles.title}>{task.title}</h2>
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
    </li>
  );
}
