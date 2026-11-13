class LoggingNotifier:
    def task_assigned(self, task_id: int, assignee_id: int) -> None:
        raise NotImplementedError
