from django.urls import path

from apps.tasks.interfaces.views import TaskCollectionView, TaskDetailView

urlpatterns = [
    path("tasks", TaskCollectionView.as_view(), name="task-list"),
    path("tasks/<int:task_id>", TaskDetailView.as_view(), name="task-detail"),
]
