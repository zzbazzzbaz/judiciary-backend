"""Cases 子应用 API（任务管理与流转）。"""

from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from utils.pagination import StandardPageNumberPagination
from utils.permissions import IsStaff
from utils.responses import error_response, success_response

from apps.users.models import User

from .models import Task
from .serializers import (
    TaskCompleteSerializer,
    TaskCreateSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskProcessSerializer,
)


class TaskViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    任务接口集合（符合需求文档路径）：
    - POST /api/v1/tasks/
    - GET /api/v1/tasks/
    - GET /api/v1/tasks/{id}/
    - POST /api/v1/tasks/{id}/process/
    - POST /api/v1/tasks/{id}/complete/
    - GET /api/v1/tasks/my-reports/
    """

    queryset = (
        Task.objects.select_related("grid", "reporter", "assigner", "assigned_mediator")
        .all()
        .order_by("-reported_at")
    )
    lookup_value_regex = r"\d+"
    pagination_class = StandardPageNumberPagination

    def get_permissions(self):
        # 管理员、网格负责人、调解员都可以上报和处理任务
        if self.action in {"create", "process", "complete", "my_reports"}:
            return [IsStaff()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return TaskListSerializer
        if self.action == "create":
            return TaskCreateSerializer
        return TaskDetailSerializer

    def _check_task_permission(self, user: User, task: Task):
        """
        任务详情权限校验（按需求文档）：
        - 管理员：可查看所有
        - 网格负责人：可查看自己网格内的任务
        - 调解员：可查看自己上报的或被分配的任务
        """

        if user.role == User.Role.ADMIN:
            return

        if user.role == User.Role.GRID_MANAGER:
            if not task.grid_id or task.grid.current_manager_id != user.id:
                raise PermissionDenied("无权查看此任务")
            return

        if user.role == User.Role.MEDIATOR:
            if task.reporter_id != user.id and task.assigned_mediator_id != user.id:
                raise PermissionDenied("无权查看此任务")
            return

        raise PermissionDenied("无权查看此任务")

    def list(self, request, *args, **kwargs):
        """任务列表（只返回指派给当前用户的任务）。"""

        qs = self.get_queryset()
        user: User = request.user

        # 所有角色都只能查看指派给自己的任务
        qs = qs.filter(assigned_mediator=user)

        params = request.query_params
        search = params.get("search")
        task_type = params.get("type")
        status_ = params.get("status")

        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(party_name__icontains=search))
        if task_type:
            qs = qs.filter(type=task_type)
        if status_:
            qs = qs.filter(status=status_)

        page = self.paginate_queryset(qs)
        serializer = TaskListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = TaskCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # code 唯一约束在并发下可能冲突：简单重试 3 次
        last_error = None
        for _ in range(3):
            try:
                with transaction.atomic():
                    task = serializer.save()
                break
            except IntegrityError as e:
                last_error = e
                continue
        else:
            raise last_error  # 交给全局异常处理

        return success_response(
            message="上报成功",
            data={
                "id": task.id,
                "code": task.code,
                "type": task.type,
                "status": task.status,
                "party_name": task.party_name,
                "reported_at": task.reported_at,
            },
        )

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        self._check_task_permission(request.user, task)
        return success_response(data=TaskDetailSerializer(task).data)

    @action(detail=True, methods=["post"], url_path="process")
    def process(self, request, pk=None):
        """提交进行中信息（调解员-被分配人）。"""

        task = self.get_object()
        user: User = request.user

        if task.assigned_mediator_id != user.id:
            return error_response("您不是该任务的负责调解员", code=403, http_status=403)
        if task.status != Task.Status.ASSIGNED:
            return error_response("任务当前状态不允许此操作", http_status=400)

        serializer = TaskProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task.participants = serializer.validated_data.get("participants")
        task.handle_method = serializer.validated_data["handle_method"]
        task.expected_plan = serializer.validated_data.get("expected_plan")
        task.process_submitted_at = timezone.now()
        task.status = Task.Status.PROCESSING
        task.save(
            update_fields=[
                "participants",
                "handle_method",
                "expected_plan",
                "process_submitted_at",
                "status",
            ]
        )

        return success_response(
            message="提交成功",
            data={
                "id": task.id,
                "code": task.code,
                "status": task.status,
                "handle_method": task.handle_method,
                "process_submitted_at": task.process_submitted_at,
            },
        )

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        """提交完成结果（调解员-被分配人）。"""

        task = self.get_object()
        user: User = request.user

        if task.assigned_mediator_id != user.id:
            return error_response("您不是该任务的负责调解员", code=403, http_status=403)
        if task.status != Task.Status.PROCESSING:
            return error_response("任务当前状态不允许此操作", http_status=400)

        serializer = TaskCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task.result = serializer.validated_data["result"]
        task.result_detail = serializer.validated_data.get("result_detail")
        task.process_description = serializer.validated_data.get("process_description")
        task.complete_lng = serializer.validated_data.get("complete_lng")
        task.complete_lat = serializer.validated_data.get("complete_lat")
        task.complete_address = serializer.validated_data.get("complete_address")
        task.complete_image_ids = serializer.validated_data.get("complete_image_ids", "") or ""
        task.complete_file_ids = serializer.validated_data.get("complete_file_ids", "") or ""
        task.completed_at = timezone.now()
        task.status = Task.Status.COMPLETED
        task.save(
            update_fields=[
                "result",
                "result_detail",
                "process_description",
                "complete_lng",
                "complete_lat",
                "complete_address",
                "complete_image_ids",
                "complete_file_ids",
                "completed_at",
                "status",
            ]
        )

        return success_response(
            message="提交成功",
            data={"id": task.id, "code": task.code, "status": task.status, "result": task.result, "completed_at": task.completed_at},
        )

    @action(detail=False, methods=["get"], url_path="my-reports")
    def my_reports(self, request):
        """我上报的任务（调解员）。"""

        qs = self.get_queryset().filter(reporter=request.user).order_by("-reported_at")

        # 获取查询参数
        search = request.query_params.get("search")
        task_type = request.query_params.get("type")
        status_ = request.query_params.get("status")

        # 关键词搜索：按任务编号或当事人姓名模糊匹配
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(party_name__icontains=search))
        if task_type:
            qs = qs.filter(type=task_type)
        if status_:
            qs = qs.filter(status=status_)

        page = self.paginate_queryset(qs)
        serializer = TaskListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .serializers import TaskMapPointSerializer


class TaskMapPointsView(APIView):
    """
    地图区域任务点查询接口（无需认证）

    - POST /api/v1/tasks/map-points/
    - 传入地图边界四个点，返回区域内的任务点
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        请求参数：
        {
            "points": [
                {"lng": 116.1, "lat": 40.1},  # 左上角
                {"lng": 116.1, "lat": 39.9},  # 左下角
                {"lng": 116.5, "lat": 40.1},  # 右上角
                {"lng": 116.5, "lat": 39.9}   # 右下角
            ]
        }
        """
        points = request.data.get("points", [])

        if len(points) != 4:
            return error_response("必须传入4个边界点", http_status=400)

        # 提取所有点的经纬度，计算边界范围
        lngs = [float(p.get("lng", 0)) for p in points]
        lats = [float(p.get("lat", 0)) for p in points]

        min_lng = min(lngs)
        max_lng = max(lngs)
        min_lat = min(lats)
        max_lat = max(lats)

        # 查询在边界范围内的任务（基于上报位置）
        tasks = Task.objects.filter(
            report_lng__gte=min_lng,
            report_lng__lte=max_lng,
            report_lat__gte=min_lat,
            report_lat__lte=max_lat,
            report_lng__isnull=False,
            report_lat__isnull=False,
        ).order_by("-reported_at")

        serializer = TaskMapPointSerializer(tasks, many=True)
        return success_response(data=serializer.data)
