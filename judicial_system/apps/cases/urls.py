"""Cases 子应用路由。"""

from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import GridTaskListView, TaskTypeListView, TaskViewSet, TownListView

router = SimpleRouter()
router.register(r"tasks", TaskViewSet, basename="tasks")

urlpatterns = [
    path("tasks/task-types/", TaskTypeListView.as_view(), name="task-type-list"),
    path("tasks/towns/", TownListView.as_view(), name="town-list"),
    path("tasks/grid-tasks/", GridTaskListView.as_view(), name="grid-task-list"),
] + router.urls
