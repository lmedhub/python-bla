import { Link, useSearchParams } from "react-router";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Pagination } from "../../components/Pagination";
import { filtersFromSearch, hasFilters, PAGE_SIZE, searchFromFilters, type TaskFilters as Filters } from "./filters";
import { useTaskPage, useUsers } from "./queries";
import { TaskFilters } from "./TaskFilters";
import { TaskItem } from "./TaskItem";
import styles from "./TaskListPage.module.css";

export function TaskListPage() {
  const [search, setSearch] = useSearchParams();
  const filters = filtersFromSearch(search);
  const tasks = useTaskPage(filters);
  const users = useUsers();

  function show(next: Filters) {
    setSearch(searchFromFilters(next));
  }

  return (
    <>
      <div className={styles.top}>
        <h1>Tasks</h1>
        <Link to="/tasks/new" className="button">
          New task
        </Link>
      </div>

      <TaskFilters
        filters={filters}
        users={users.data}
        // A new filter changes what "page 3" means, so start again at page 1.
        onChange={(changes) => {
          show({ ...filters, ...changes, page: 1 });
        }}
        onClear={() => {
          show({ page: 1 });
        }}
      />

      {tasks.isPending ? (
        <p role="status">Loading tasks…</p>
      ) : tasks.isError ? (
        <ErrorMessage error={tasks.error} onRetry={() => void tasks.refetch()} />
      ) : tasks.data.count === 0 ? (
        <p>{hasFilters(filters) ? "No tasks match these filters." : "No tasks yet."}</p>
      ) : tasks.data.results.length === 0 ? (
        // A shared or old link can point past the last page.
        <p>
          This page is empty.{" "}
          <button
            type="button"
            className="link"
            onClick={() => {
              show({ ...filters, page: 1 });
            }}
          >
            Go to the first page
          </button>
        </p>
      ) : (
        <>
          <ul className={styles.list}>
            {tasks.data.results.map((task) => (
              <TaskItem key={task.id} task={task} users={users.data} />
            ))}
          </ul>
          {tasks.data.count > PAGE_SIZE && (
            <Pagination
              page={filters.page}
              totalPages={Math.ceil(tasks.data.count / PAGE_SIZE)}
              onChange={(page) => {
                show({ ...filters, page });
              }}
            />
          )}
        </>
      )}
    </>
  );
}
