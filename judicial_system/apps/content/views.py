"""
Content 子应用 API

接口：
- GET  /api/v1/content/categories/           分类列表（登录用户）
- 管理端文章：
  - /api/v1/articles/                        列表/创建（管理员）
  - /api/v1/articles/{id}/                   详情/更新/删除（管理员）
  - /api/v1/articles/{id}/publish/           发布（管理员）
  - /api/v1/articles/{id}/archive/           下架（管理员）
- 移动端文章：
  - /api/v1/articles/published/              已发布文章列表（登录用户）
  - /api/v1/articles/{id}/detail/            已发布文章详情（登录用户）
"""

from __future__ import annotations

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.pagination import StandardPageNumberPagination
from utils.permissions import IsAdmin
from utils.responses import error_response, success_response

from .models import Article, Category
from .serializers import (
    ArticleCreateSerializer,
    ArticleDetailSerializer,
    ArticleListSerializer,
    ArticlePublishedDetailSerializer,
    ArticlePublishedListSerializer,
    ArticleUpdateSerializer,
    CategorySerializer,
)


class ContentMobilePagination(StandardPageNumberPagination):
    """移动端默认分页：page_size=10。"""

    page_size = 10


class CategoryListAPIView(APIView):
    """分类列表（登录用户）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all().order_by("sort_order", "id")
        return success_response(data=CategorySerializer(categories, many=True).data)


class ArticleViewSet(viewsets.ModelViewSet):
    """文章管理与展示。"""

    queryset = Article.objects.select_related("category", "publisher").all()
    pagination_class = StandardPageNumberPagination

    def get_permissions(self):
        if self.action in {"published", "mobile_detail"}:
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == "list":
            return ArticleListSerializer
        if self.action == "create":
            return ArticleCreateSerializer
        if self.action in {"update", "partial_update"}:
            return ArticleUpdateSerializer
        if self.action == "published":
            return ArticlePublishedListSerializer
        if self.action == "mobile_detail":
            return ArticlePublishedDetailSerializer
        return ArticleDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            return qs

        params = self.request.query_params
        search = params.get("search")
        category_id = params.get("category_id")
        status_ = params.get("status")

        if search:
            qs = qs.filter(Q(title__icontains=search))
        if category_id and str(category_id).isdigit():
            qs = qs.filter(category_id=int(category_id))
        if status_:
            qs = qs.filter(status=status_)

        return qs.order_by("-sort_order", "-created_at")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        serializer = ArticleListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = ArticleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        return success_response(
            message="创建成功",
            data={
                "id": article.id,
                "title": article.title,
                "category_id": article.category_id,
                "status": article.status,
                "created_at": article.created_at,
            },
            http_status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=ArticleDetailSerializer(instance).data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ArticleUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        return success_response(
            message="更新成功",
            data={"id": instance.id, "title": instance.title, "updated_at": instance.updated_at},
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="删除成功", http_status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        """发布文章（管理员）。"""

        article = self.get_object()
        if article.status == Article.Status.PUBLISHED:
            return error_response("文章已发布，无需重复操作", http_status=400)

        if article.status not in {Article.Status.DRAFT, Article.Status.ARCHIVED}:
            return error_response("文章状态不允许发布", http_status=400)

        article.status = Article.Status.PUBLISHED
        article.publisher = request.user
        article.published_at = timezone.now()
        article.save(update_fields=["status", "publisher", "published_at"])

        return success_response(
            message="发布成功",
            data={"id": article.id, "status": article.status, "published_at": article.published_at},
        )

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """下架文章（管理员）。"""

        article = self.get_object()
        if article.status != Article.Status.PUBLISHED:
            return error_response("只能下架已发布的文章", http_status=400)

        article.status = Article.Status.ARCHIVED
        article.save(update_fields=["status"])

        return success_response(message="下架成功", data={"id": article.id, "status": article.status})

    @action(detail=False, methods=["get"], url_path="published")
    def published(self, request):
        """已发布文章列表（移动端）。"""

        qs = Article.objects.select_related("category").filter(status=Article.Status.PUBLISHED)

        category_id = request.query_params.get("category_id")
        if category_id and str(category_id).isdigit():
            qs = qs.filter(category_id=int(category_id))

        qs = qs.order_by("-sort_order", "-published_at")

        paginator = ContentMobilePagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = ArticlePublishedListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"], url_path="detail")
    def mobile_detail(self, request, pk=None):
        """文章详情（移动端，必须已发布）。"""

        article = (
            Article.objects.select_related("category")
            .filter(id=pk, status=Article.Status.PUBLISHED)
            .first()
        )
        if not article:
            return error_response("文章不存在或未发布", code=404, http_status=404)

        return success_response(data=ArticlePublishedDetailSerializer(article).data)
