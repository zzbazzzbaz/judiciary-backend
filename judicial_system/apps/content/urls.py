"""Content 子应用路由。"""

from rest_framework.routers import SimpleRouter

from .views import ActivityViewSet, ArticleViewSet, CategoryViewSet, DocumentViewSet

router = SimpleRouter()
router.register(r"articles", ArticleViewSet, basename="articles")
router.register(r"activities", ActivityViewSet, basename="activities")
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"documents", DocumentViewSet, basename="documents")

urlpatterns = router.urls
