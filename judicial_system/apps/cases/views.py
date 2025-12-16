"""Cases 子应用 API（任务管理与流转）。"""

from __future__ import annotations

from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from utils.pagination import StandardPageNumberPagination
from utils.permissions import IsMediator
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


class TaskViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    任务接口集合（符合需求文档路径）：
    - /api/v1/tasks/
    - /api/v1/tasks/{id}/
    - /api/v1/tasks/{id}/process/
    - /api/v1/tasks/{id}/complete/
    - /api/v1/tasks/my-reports/
    - /api/v1/tasks/my-tasks/
    - /api/v1/tasks/my-history/
    - /api/v1/tasks/my-tasks/{id}/
    """

    queryset = (
        Task.objects.select_related("grid", "reporter", "assigner", "assigned_mediator")
        .all()
        .order_by("-reported_at")
    )
    pagination_class = StandardPageNumberPagination

    def get_permissions(self):
        if self.action == "create":
            return [IsMediator()]
        if self.action in {"process", "complete", "my_reports", "my_tasks", "my_history", "my_task_detail"}:
            return [IsMediator()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
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
        task_type = request.query_params.get("type")
        status_ = request.query_params.get("status")
        if task_type:
            qs = qs.filter(type=task_type)
        if status_:
            qs = qs.filter(status=status_)

        page = self.paginate_queryset(qs)
        serializer = TaskListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my-tasks")
    def my_tasks(self, request):
        """我的待办任务（调解员）。"""

        qs = self.get_queryset().filter(assigned_mediator=request.user).order_by("-assigned_at", "-reported_at")
        task_type = request.query_params.get("type")
        status_ = request.query_params.get("status")

        if task_type:
            qs = qs.filter(type=task_type)
        if status_:
            qs = qs.filter(status=status_)
        else:
            qs = qs.filter(status__in=[Task.Status.ASSIGNED, Task.Status.PROCESSING])

        page = self.paginate_queryset(qs)
        serializer = TaskListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my-history")
    def my_history(self, request):
        """我的历史任务（调解员）。"""

        qs = (
            self.get_queryset()
            .filter(assigned_mediator=request.user, status=Task.Status.COMPLETED)
            .order_by("-completed_at", "-reported_at")
        )

        task_type = request.query_params.get("type")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if task_type:
            qs = qs.filter(type=task_type)

        try:
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                qs = qs.filter(completed_at__date__gte=start)
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                qs = qs.filter(completed_at__date__lte=end)
        except ValueError:
            return error_response("日期格式不正确（YYYY-MM-DD）", http_status=400)

        page = self.paginate_queryset(qs)
        serializer = TaskListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"my-tasks/(?P<pk>[^/.]+)")
    def my_task_detail(self, request, pk=None):
        """调解员任务详情（/tasks/my-tasks/{id}/）。"""

        if not pk or not str(pk).isdigit():
            return error_response("任务不存在", code=404, http_status=404)
        task = self.get_queryset().filter(id=int(pk)).first()
        if not task:
            return error_response("任务不存在", code=404, http_status=404)

        # 调解员仅能查看自己上报的或被分配的任务
        if task.reporter_id != request.user.id and task.assigned_mediator_id != request.user.id:
            return error_response("无权查看此任务", code=403, http_status=403)

        return success_response(data=TaskDetailSerializer(task).data)
