import pytest

from apps.core.domain.errors import NotFoundError, PermissionDeniedError
from apps.tasks.application.queries import PageRequest, TaskFilter
from apps.tasks.application.use_cases import DeleteTask, GetTask, ListTasks
from apps.tasks.domain.task import Task, TaskStatus
from apps.tasks.tests.application.constants import ASSIGNEE, CREATOR, NOW, STRANGER
from apps.tasks.tests.fakes import InMemoryTaskRepository


@pytest.fixture
def task(tasks: InMemoryTaskRepository) -> Task:
    return tasks.add(Task(title="Write tests", created_by_id=CREATOR, assignee_id=ASSIGNEE))


class TestGetTask:
    def test_returns_the_task(self, tasks, task):
        assert GetTask(tasks=tasks).execute(task.require_id()) == task

    def test_unknown_task_is_not_found(self, tasks):
        with pytest.raises(NotFoundError):
            GetTask(tasks=tasks).execute(999)


class TestListTasks:
    def test_passes_the_filter_the_page_and_todays_date_to_the_repository(self, tasks, clock):
        task_filter = TaskFilter(status=TaskStatus.TODO, overdue=True)
        page = PageRequest(page=2, page_size=5)

        result = ListTasks(tasks=tasks, clock=clock).execute(task_filter, page)

        assert tasks.find_calls == [(task_filter, page, NOW.date())]
        assert result.request == page


class TestDeleteTask:
    def test_creator_deletes_the_task(self, tasks, task):
        DeleteTask(tasks=tasks).execute(actor_id=CREATOR, task_id=task.require_id())

        assert tasks.get(task.require_id()) is None

    @pytest.mark.parametrize("actor_id", [ASSIGNEE, STRANGER])
    def test_nobody_else_may_delete(self, tasks, task, actor_id):
        with pytest.raises(PermissionDeniedError):
            DeleteTask(tasks=tasks).execute(actor_id=actor_id, task_id=task.require_id())

        assert tasks.get(task.require_id()) is not None

    def test_unknown_task_is_not_found(self, tasks):
        with pytest.raises(NotFoundError):
            DeleteTask(tasks=tasks).execute(actor_id=CREATOR, task_id=999)
