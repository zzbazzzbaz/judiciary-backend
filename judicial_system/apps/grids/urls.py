"""Grids 子应用路由。"""

from rest_framework.routers import DefaultRouter

from .views import GridViewSet

router = DefaultRouter()
router.register(r"grids", GridViewSet, basename="grids")

urlpatterns = router.urls

