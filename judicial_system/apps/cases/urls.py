"""Cases 子应用路由。"""

from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import TaskMapPointsView, TaskViewSet

router = SimpleRouter()
router.register(r"tasks", TaskViewSet, basename="tasks")

urlpatterns = [
    path("tasks/map-points/", TaskMapPointsView.as_view(), name="task-map-points"),
] + router.urls
