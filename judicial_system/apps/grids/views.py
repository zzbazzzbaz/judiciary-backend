"""
Grids 子应用 API

包含：
- 网格 CRUD
- 负责人设置
- 调解员分配管理
- 地图数据与统计
"""

from __future__ import annotations

from datetime import datetime

from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from utils.pagination import StandardPageNumberPagination
from utils.permissions import IsAdmin, IsGridManager
from utils.responses import error_response, success_response
from utils.validators import parse_bool

from apps.users.models import User

from .models import Grid, MediatorAssignment
from .serializers import (
    GridCreateUpdateSerializer,
    GridDetailSerializer,
    GridListSerializer,
    GridManagerUpdateSerializer,
    MediatorAddSerializer,
)


class GridViewSet(viewsets.ModelViewSet):
    """
    网格管理接口集合（符合需求文档路径）：
    - /api/v1/grids/
    - /api/v1/grids/{id}/
    - /api/v1/grids/{id}/manager/
    - /api/v1/grids/{id}/mediators/
    - /api/v1/grids/{id}/mediators/{uid}/
    - /api/v1/grids/map-data/
    - /api/v1/grids/{id}/statistics/
    """

    pagination_class = StandardPageNumberPagination
    queryset = (
        Grid.objects.select_related("current_manager")
        .annotate(mediator_count=Count("mediator_assignments", distinct=True))
        .order_by("-created_at")
    )

    def get_permissions(self):
        # 管理员专属接口
        admin_actions = {
            "list",
            "create",
            "update",
            "partial_update",
            "destroy",
            "manager",
            "mediators_remove",
            "map_data",
        }
        if self.action in admin_actions or (self.action == "mediators" and self.request.method == "POST"):
            return [IsAdmin()]

        # 管理员/网格负责人（受限到自己网格）
        return [IsGridManager()]

    def get_serializer_class(self):
        if self.action == "list":
            return GridListSerializer
        if self.action in {"create", "update", "partial_update"}:
            return GridCreateUpdateSerializer
        return GridDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            return qs

        params = self.request.query_params
        search = params.get("search")
        is_active = parse_bool(params.get("is_active"))

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(region__icontains=search))
        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        return qs

    def _check_grid_manager_permission(self, grid: Grid):
        """
        网格负责人权限校验：
        - admin 可查看所有
        - grid_manager 仅可查看自己负责的网格
        """

        user = self.request.user
        if user.role == User.Role.ADMIN:
            return
        if grid.current_manager_id != user.id:
            raise PermissionDenied("无权访问该网格")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self._check_grid_manager_permission(instance)
        return success_response(data=GridDetailSerializer(instance).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grid = serializer.save()
        # 重新加载注解字段
        grid = (
            Grid.objects.select_related("current_manager")
            .annotate(mediator_count=Count("mediator_assignments", distinct=True))
            .get(id=grid.id)
        )
        return success_response(message="创建成功", data=GridDetailSerializer(grid).data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        instance = (
            Grid.objects.select_related("current_manager")
            .annotate(mediator_count=Count("mediator_assignments", distinct=True))
            .get(id=instance.id)
        )
        return success_response(message="更新成功", data=GridDetailSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        instance = (
            Grid.objects.select_related("current_manager")
            .annotate(mediator_count=Count("mediator_assignments", distinct=True))
            .get(id=instance.id)
        )
        return success_response(message="更新成功", data=GridDetailSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 检查是否有关联未完成任务
        from apps.cases.models import Task

        has_unfinished = Task.objects.filter(grid=instance).exclude(status=Task.Status.COMPLETED).exists()
        if has_unfinished:
            return error_response("该网格下存在未完成的任务，无法删除", http_status=400)

        # 删除调解员分配记录
        MediatorAssignment.objects.filter(grid=instance).delete()

        # 软删除网格（保留历史数据）
        instance.is_active = False
        instance.save(update_fields=["is_active"])

        return success_response(message="删除成功", http_status=status.HTTP_200_OK)

    @action(detail=True, methods=["put"], url_path="manager")
    def manager(self, request, pk=None):
        """设置/清除负责人（管理员）。"""

        grid = self.get_object()
        serializer = GridManagerUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        manager_id = serializer.validated_data.get("manager_id")
        if manager_id is None:
            grid.current_manager = None
            grid.save(update_fields=["current_manager"])
            return success_response(
                message="设置成功",
                data={"id": grid.id, "name": grid.name, "current_manager": None},
            )

        manager = User.objects.filter(id=manager_id).first()
        if not manager:
            return error_response("用户不存在", code=404, http_status=404)
        if manager.role != User.Role.GRID_MANAGER:
            return error_response("该用户不是网格负责人角色", http_status=400)
        if not manager.is_active:
            return error_response("该用户已被禁用", http_status=400)

        grid.current_manager = manager
        grid.save(update_fields=["current_manager"])
        return success_response(
            message="设置成功",
            data={"id": grid.id, "name": grid.name, "current_manager": {"id": manager.id, "name": manager.name}},
        )

    @action(detail=True, methods=["get", "post"], url_path="mediators")
    def mediators(self, request, pk=None):
        """GET 网格内调解员列表；POST 添加调解员到网格。"""

        grid = self.get_object()
        if request.method == "GET":
            self._check_grid_manager_permission(grid)

            search = request.query_params.get("search")

            assignments = (
                MediatorAssignment.objects.filter(grid=grid)
                .select_related("mediator", "mediator__organization")
                .order_by("-created_at")
            )
            if search:
                assignments = assignments.filter(
                    Q(mediator__name__icontains=search) | Q(mediator__phone__icontains=search)
                )

            mediator_ids = list(assignments.values_list("mediator_id", flat=True))

            # 统计每个调解员在该网格的任务数量（总数/已完成）
            from apps.cases.models import Task

            task_stats = (
                Task.objects.filter(grid=grid, assigned_mediator_id__in=mediator_ids)
                .values("assigned_mediator_id")
                .annotate(
                    task_count=Count("id"),
                    completed_count=Count("id", filter=Q(status=Task.Status.COMPLETED)),
                )
            )
            stats_map = {row["assigned_mediator_id"]: row for row in task_stats}

            data = []
            for a in assignments:
                mediator = a.mediator
                stats = stats_map.get(mediator.id, {})
                data.append(
                    {
                        "id": mediator.id,
                        "name": mediator.name,
                        "phone": mediator.phone,
                        "organization_name": mediator.organization.name if mediator.organization else None,
                        "task_count": stats.get("task_count", 0),
                        "completed_count": stats.get("completed_count", 0),
                        "assigned_at": a.created_at,
                    }
                )

            return success_response(data=data)

        # POST：管理员添加调解员到网格
        serializer = MediatorAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mediator_id = serializer.validated_data["mediator_id"]

        mediator = User.objects.filter(id=mediator_id).first()
        if not mediator:
            return error_response("调解员不存在", code=404, http_status=404)
        if mediator.role != User.Role.MEDIATOR:
            return error_response("该用户不是调解员角色", http_status=400)
        if not mediator.is_active:
            return error_response("该调解员已被禁用", http_status=400)

        if MediatorAssignment.objects.filter(grid=grid, mediator=mediator).exists():
            return error_response("该调解员已分配到此网格", http_status=400)

        assignment = MediatorAssignment.objects.create(grid=grid, mediator=mediator)
        return success_response(
            message="添加成功",
            data={
                "grid_id": grid.id,
                "mediator_id": mediator.id,
                "mediator_name": mediator.name,
                "assigned_at": assignment.created_at,
            },
        )

    @action(detail=True, methods=["delete"], url_path=r"mediators/(?P<uid>[^/.]+)")
    def mediators_remove(self, request, pk=None, uid=None):
        """移除调解员（管理员）。"""

        grid = self.get_object()
        if not uid or not str(uid).isdigit():
            return error_response("参数 uid 不正确", http_status=400)
        mediator_id = int(uid)

        assignment = MediatorAssignment.objects.filter(grid=grid, mediator_id=mediator_id).first()
        if not assignment:
            return error_response("该调解员未分配到此网格", code=404, http_status=404)

        from apps.cases.models import Task

        has_unfinished = (
            Task.objects.filter(grid=grid, assigned_mediator_id=mediator_id)
            .exclude(status=Task.Status.COMPLETED)
            .exists()
        )
        if has_unfinished:
            return error_response("该调解员在此网格有未完成的任务", http_status=400)

        assignment.delete()
        return success_response(message="移除成功", http_status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="map-data")
    def map_data(self, request):
        """地图展示数据（管理员）。"""

        is_active = parse_bool(request.query_params.get("is_active"))
        qs = Grid.objects.select_related("current_manager").annotate(
            mediator_count=Count("mediator_assignments", distinct=True),
        )
        if is_active is None:
            qs = qs.filter(is_active=True)
        else:
            qs = qs.filter(is_active=is_active)

        from apps.cases.models import Task

        # 任务数量（按网格聚合）
        task_counts = (
            Task.objects.filter(grid_id__in=qs.values_list("id", flat=True))
            .values("grid_id")
            .annotate(task_count=Count("id"))
        )
        task_count_map = {row["grid_id"]: row["task_count"] for row in task_counts}

        data = []
        for grid in qs.order_by("-created_at"):
            data.append(
                {
                    "id": grid.id,
                    "name": grid.name,
                    "boundary": grid.boundary,
                    "center_lng": grid.center_lng,
                    "center_lat": grid.center_lat,
                    "manager_name": grid.current_manager.name if grid.current_manager else None,
                    "mediator_count": grid.mediator_count,
                    "task_count": task_count_map.get(grid.id, 0),
                }
            )

        return success_response(data=data)

    @action(detail=True, methods=["get"], url_path="statistics")
    def statistics(self, request, pk=None):
        """网格统计数据（管理员/该网格负责人）。"""

        grid = self.get_object()
        self._check_grid_manager_permission(grid)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        from apps.cases.models import Task

        qs = Task.objects.filter(grid=grid)
        # 可选日期过滤（按 reported_at 的日期部分）
        try:
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                qs = qs.filter(reported_at__date__gte=start)
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                qs = qs.filter(reported_at__date__lte=end)
        except ValueError:
            return error_response("日期格式不正确（YYYY-MM-DD）", http_status=400)

        mediator_count = MediatorAssignment.objects.filter(grid=grid).count()

        task_summary = qs.aggregate(
            total=Count("id"),
            dispute=Count("id", filter=Q(type=Task.Type.DISPUTE)),
            legal_aid=Count("id", filter=Q(type=Task.Type.LEGAL_AID)),
        )
        status_summary = qs.aggregate(
            reported=Count("id", filter=Q(status=Task.Status.REPORTED)),
            assigned=Count("id", filter=Q(status=Task.Status.ASSIGNED)),
            processing=Count("id", filter=Q(status=Task.Status.PROCESSING)),
            completed=Count("id", filter=Q(status=Task.Status.COMPLETED)),
        )

        return success_response(
            data={
                "grid_id": grid.id,
                "grid_name": grid.name,
                "mediator_count": mediator_count,
                "task_summary": task_summary,
                "status_summary": status_summary,
            }
        )
