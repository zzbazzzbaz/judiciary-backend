"""网格路由配置"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GridViewSet

router = DefaultRouter()
router.register(r"grids", GridViewSet, basename="grid")

urlpatterns = [
    path("", include(router.urls)),
]
