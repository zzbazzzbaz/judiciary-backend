"""Content 子应用 API。"""

from __future__ import annotations

from django.db import models
from django.db.models import Count, Exists, OuterRef
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from utils.responses import error_response, success_response

from .models import Activity, Article, Category
from .serializers import (
    ActivityDetailSerializer,
    ActivityListSerializer,
    ArticleDetailSerializer,
    ArticleListSerializer,
    CategorySerializer,
)


class ArticleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    文章接口：
    - GET /api/v1/articles/
    - GET /api/v1/articles/{id}/
    """

    lookup_value_regex = r"\d+"

    def get_queryset(self):
        return (
            Article.objects.select_related("category", "publisher")
            .prefetch_related("files")
            .filter(status=Article.Status.PUBLISHED)
            .order_by("sort_order", "-published_at", "-id")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ArticleListSerializer
        return ArticleDetailSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        params = request.query_params
        search = params.get("search")
        category_id = params.get("category_id")

        if search:
            qs = qs.filter(title__icontains=search)
        if category_id and str(category_id).isdigit():
            qs = qs.filter(category_id=int(category_id))

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        article = self.get_object()
        return success_response(data=self.get_serializer(article).data)


class ActivityViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    活动接口：
    - GET  /api/v1/activities/
    - GET  /api/v1/activities/{id}/
    - POST /api/v1/activities/{id}/join/
    """

    lookup_value_regex = r"\d+"

    def get_queryset(self):
        qs = (
            Activity.objects.prefetch_related("files")
            .annotate(participant_count=Count("participants", distinct=True))
            .order_by("-created_at", "-id")
        )

        user = getattr(self.request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            through = Activity.participants.through
            qs = qs.annotate(
                is_joined=Exists(through.objects.filter(activity_id=OuterRef("pk"), user_id=user.id))
            )
        else:
            qs = qs.annotate(is_joined=models.Value(False, output_field=models.BooleanField()))

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ActivityListSerializer
        return ActivityDetailSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        activity = self.get_object()
        return success_response(data=self.get_serializer(activity).data)

    @action(detail=True, methods=["post"], url_path="join")
    def join(self, request, pk=None):
        """参与/报名活动（当前登录用户）。"""

        activity: Activity = self.get_object()
        now = timezone.now()

        if activity.registration_start and now < activity.registration_start:
            return error_response("报名未开始", http_status=400)
        if activity.registration_end and now > activity.registration_end:
            return error_response("报名已结束", http_status=400)

        user = request.user
        activity.participants.add(user)

        return success_response(
            message="报名成功",
            data={
                "id": activity.id,
                "is_joined": True,
                "participant_count": activity.participants.count(),
            },
        )


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    分类接口：
    - GET /api/v1/categories/
    """

    queryset = Category.objects.all().order_by("sort_order", "id")
    serializer_class = CategorySerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)
        return success_response(data=self.get_serializer(qs, many=True).data)
