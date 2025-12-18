"""Cases 子应用路由。"""

from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import GridTaskListView, TaskViewSet

router = SimpleRouter()
router.register(r"tasks", TaskViewSet, basename="tasks")

urlpatterns = [
    path("tasks/grid-tasks/", GridTaskListView.as_view(), name="grid-task-list"),
] + router.urls
