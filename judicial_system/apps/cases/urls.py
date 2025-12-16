"""Cases 子应用路由。"""

from rest_framework.routers import SimpleRouter

from .views import TaskViewSet

router = SimpleRouter()
router.register(r"tasks", TaskViewSet, basename="tasks")

urlpatterns = router.urls
