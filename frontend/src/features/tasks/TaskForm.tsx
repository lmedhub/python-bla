import { useState, type ReactNode, type SubmitEvent } from "react";
import { Link } from "react-router";
import { ApiError, userMessage } from "../../api/errors";
import { isTaskStatus, TASK_STATUSES, type TaskStatus, type User } from "../../api/types";
import { STATUS_LABELS } from "./status";
import styles from "./TaskForm.module.css";

/** What the inputs hold. Empty strings mean "none" for the date and the assignee. */
export interface TaskFormValues {
  title: string;
  description: string;
  dueDate: string;
  assignee: string;
  status: TaskStatus;
}

export const EMPTY_TASK: TaskFormValues = {
  title: "",
  description: "",
  dueDate: "",
  assignee: "",
  status: "todo",
};

interface TaskFormProps {
  initial: TaskFormValues;
  users: User[] | undefined;
  submitLabel: string;
  /** Status is chosen on edit only: a new task always starts as "to do". */
  showStatus: boolean;
  /** Earliest due date the date picker offers (the API enforces it too). */
  minDueDate?: string;
  /** Rejects with an ApiError to show the server's field errors. */
  onSubmit: (values: TaskFormValues) => Promise<void>;
}

export function TaskForm({ initial, users, submitLabel, showStatus, minDueDate, onSubmit }: TaskFormProps) {
  const [values, setValues] = useState(initial);
  const [error, setError] = useState<unknown>(null);
  const [submitting, setSubmitting] = useState(false);
  const fieldErrors = error instanceof ApiError ? error.fields : {};

  function set<K extends keyof TaskFormValues>(name: K, value: TaskFormValues[K]) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(values);
    } catch (caught) {
      setError(caught);
      setSubmitting(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={(event) => void handleSubmit(event)}>
      {error !== null && (
        <p role="alert" className={styles.formError}>
          {userMessage(error)}
        </p>
      )}

      <Field id="task-title" label="Title" errors={fieldErrors.title}>
        {(errorProps) => (
          <input
            id="task-title"
            required
            maxLength={200}
            value={values.title}
            onChange={(event) => {
              set("title", event.target.value);
            }}
            {...errorProps}
          />
        )}
      </Field>

      <Field id="task-description" label="Description" errors={fieldErrors.description}>
        {(errorProps) => (
          <textarea
            id="task-description"
            rows={4}
            value={values.description}
            onChange={(event) => {
              set("description", event.target.value);
            }}
            {...errorProps}
          />
        )}
      </Field>

      <Field id="task-due-date" label="Due date" errors={fieldErrors.due_date}>
        {(errorProps) => (
          <input
            id="task-due-date"
            type="date"
            min={minDueDate}
            value={values.dueDate}
            onChange={(event) => {
              set("dueDate", event.target.value);
            }}
            {...errorProps}
          />
        )}
      </Field>

      <Field id="task-assignee" label="Assignee" errors={fieldErrors.assignee}>
        {(errorProps) => (
          <select
            id="task-assignee"
            value={values.assignee}
            onChange={(event) => {
              set("assignee", event.target.value);
            }}
            {...errorProps}
          >
            <option value="">Unassigned</option>
            {users?.map((user) => (
              <option key={user.id} value={String(user.id)}>
                {user.name}
              </option>
            ))}
          </select>
        )}
      </Field>

      {showStatus && (
        <Field id="task-status" label="Status" errors={fieldErrors.status}>
          {(errorProps) => (
            <select
              id="task-status"
              value={values.status}
              onChange={(event) => {
                const { value } = event.target;
                if (isTaskStatus(value)) set("status", value);
              }}
              {...errorProps}
            >
              {TASK_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {STATUS_LABELS[status]}
                </option>
              ))}
            </select>
          )}
        </Field>
      )}

      <div className={styles.actions}>
        <button type="submit" disabled={submitting}>
          {submitLabel}
        </button>
        <Link to="/tasks">Cancel</Link>
      </div>
    </form>
  );
}

interface ErrorProps {
  "aria-invalid"?: true;
  "aria-describedby"?: string;
}

/** A label, an input, and the server's messages for it, linked for screen readers. */
function Field({
  id,
  label,
  errors,
  children,
}: {
  id: string;
  label: string;
  errors: string[] | undefined;
  children: (errorProps: ErrorProps) => ReactNode;
}) {
  const errorId = `${id}-error`;
  const hasErrors = errors !== undefined && errors.length > 0;
  return (
    <div className={styles.field}>
      <label htmlFor={id}>{label}</label>
      {children(hasErrors ? { "aria-invalid": true, "aria-describedby": errorId } : {})}
      {hasErrors && (
        <p id={errorId} className={styles.fieldError}>
          {errors.join(" ")}
        </p>
      )}
    </div>
  );
}
