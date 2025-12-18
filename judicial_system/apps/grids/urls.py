"""网格路由配置"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GridCreateView, GridViewSet

router = DefaultRouter()
router.register(r"grids", GridViewSet, basename="grid")

urlpatterns = [
    path("grids/create/", GridCreateView.as_view(), name="grid-create"),
    path("", include(router.urls)),
]
