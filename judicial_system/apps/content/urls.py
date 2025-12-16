"""Content 子应用路由。"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet, CategoryListAPIView

router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="articles")

urlpatterns = [
    path("content/categories/", CategoryListAPIView.as_view(), name="content-categories"),
    path("", include(router.urls)),
]

