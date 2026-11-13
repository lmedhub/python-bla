import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { ApiError } from "../../api/errors";
import type { Task } from "../../api/types";
import { ErrorMessage } from "../../components/ErrorMessage";
import { todayIso } from "../../lib/dates";
import { useCurrentUser } from "../auth/AuthProvider";
import { canEdit } from "./permissions";
import { taskKeys, useCreateTask, useTask, useUpdateTask, useUsers } from "./queries";
import { EMPTY_TASK, TaskForm, type TaskFormValues } from "./TaskForm";

/** /tasks/new creates; /tasks/:taskId/edit edits. */
export function TaskFormPage() {
  const { taskId } = useParams();
  if (taskId === undefined) {
    return <CreateTask />;
  }
  const id = Number(taskId);
  if (!Number.isInteger(id) || id < 1) {
    return <p role="alert">Task not found.</p>;
  }
  return <EditTask taskId={id} />;
}

function CreateTask() {
  const navigate = useNavigate();
  const users = useUsers();
  const create = useCreateTask();

  return (
    <>
      <h1>New task</h1>
      <TaskForm
        initial={EMPTY_TASK}
        users={users.data}
        submitLabel="Create task"
        showStatus={false}
        minDueDate={todayIso()}
        onSubmit={async (values) => {
          await create.mutateAsync({
            title: values.title,
            description: values.description,
            due_date: values.dueDate || null,
            assignee: values.assignee ? Number(values.assignee) : null,
          });
          await navigate("/tasks");
        }}
      />
    </>
  );
}

const CONFLICT_MESSAGE =
  "Someone else changed this task. The form now shows their version; make your change again.";

function EditTask({ taskId }: { taskId: number }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const currentUser = useCurrentUser();
  const task = useTask(taskId);
  const users = useUsers();
  const update = useUpdateTask();
  const [conflict, setConflict] = useState(false);

  if (task.isPending) {
    return <p role="status">Loading task…</p>;
  }
  if (task.isError) {
    return <ErrorMessage error={task.error} />;
  }
  if (!canEdit(task.data, currentUser.id)) {
    return (
      <>
        <h1>{task.data.title}</h1>
        <p>Only the person who created this task can edit it.</p>
        <Link to="/tasks">Back to tasks</Link>
      </>
    );
  }

  async function save(values: TaskFormValues, version: number) {
    try {
      await update.mutateAsync({
        taskId,
        changes: {
          title: values.title,
          description: values.description,
          due_date: values.dueDate || null,
          assignee: values.assignee ? Number(values.assignee) : null,
          status: values.status,
          // Without this, a save would silently overwrite a newer change (ADR 0010).
          version,
        },
      });
      await navigate("/tasks");
    } catch (caught) {
      if (caught instanceof ApiError && caught.code === "conflict") {
        setConflict(true);
        await queryClient.invalidateQueries({ queryKey: taskKeys.detail(taskId) });
        return;
      }
      throw caught;
    }
  }

  return (
    <>
      <h1>Edit task</h1>
      {conflict && <p role="alert">{CONFLICT_MESSAGE}</p>}
      <TaskForm
        // A new version remounts the form, so it starts from the newest saved values.
        key={task.data.version}
        initial={formValues(task.data)}
        users={users.data}
        submitLabel="Save changes"
        showStatus
        onSubmit={(values) => save(values, task.data.version)}
      />
    </>
  );
}

function formValues(task: Task): TaskFormValues {
  return {
    title: task.title,
    description: task.description,
    dueDate: task.due_date ?? "",
    assignee: task.assignee === null ? "" : String(task.assignee),
    status: task.status,
  };
}
