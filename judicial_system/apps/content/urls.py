"""Content 子应用路由。"""

from rest_framework.routers import SimpleRouter

from .views import ActivityViewSet, ArticleViewSet, CategoryViewSet, DocumentCategoryViewSet, DocumentViewSet

router = SimpleRouter()
router.register(r"articles", ArticleViewSet, basename="articles")
router.register(r"activities", ActivityViewSet, basename="activities")
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"documents", DocumentViewSet, basename="documents")
router.register(r"document-categories", DocumentCategoryViewSet, basename="document-categories")

urlpatterns = router.urls
