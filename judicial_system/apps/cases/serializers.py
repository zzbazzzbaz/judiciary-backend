"""
Cases 子应用序列化器

说明：
- Task 创建时会自动生成 code，并校验附件 ID 是否存在。
- Task 详情输出会解析附件字段，返回附件详情列表。
"""

from __future__ import annotations

from rest_framework import serializers

from utils.attachment_utils import get_attachments_by_ids, parse_attachment_ids
from utils.url_utils import get_absolute_url
from utils.code_generator import generate_task_code

from apps.common.models import Attachment
from apps.grids.models import Grid
from apps.users.models import User

from .models import Task, TaskType, Town


class UserNameSerializer(serializers.ModelSerializer):
    """用户简要信息（id/name）。"""

    class Meta:
        model = User
        fields = ["id", "name"]


class GridSimpleSerializer(serializers.ModelSerializer):
    """网格简要信息（id/name）。"""

    class Meta:
        model = Grid
        fields = ["id", "name"]


class TaskTypeSerializer(serializers.ModelSerializer):
    """任务类型序列化器。"""

    class Meta:
        model = TaskType
        fields = ["id", "name", "code", "description"]


class TownSerializer(serializers.ModelSerializer):
    """所属镇序列化器。"""

    class Meta:
        model = Town
        fields = ["id", "name", "code", "description"]


class TaskListSerializer(serializers.ModelSerializer):
    """任务列表项"""

    task_type_name = serializers.CharField(source="task_type.name", read_only=True, default=None)
    town_name = serializers.CharField(source="town.name", read_only=True, default=None)
    grid_name = serializers.CharField(source="grid.name", read_only=True)
    reporter_name = serializers.CharField(source="reporter.name", read_only=True)
    assigned_mediator_name = serializers.CharField(source="assigned_mediator.name", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "code",
            "task_type_name",
            "town_name",
            "status",
            "party_name",
            "party_phone",
            "description",
            "amount",
            "grid_name",
            "reporter_name",
            "assigned_mediator_name",
            "reported_at",
            "assigned_at",
            "report_lng",
            "report_lat",
            "report_address",
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """任务详情。"""

    task_type = TaskTypeSerializer(read_only=True)
    town = TownSerializer(read_only=True)
    grid = GridSimpleSerializer(read_only=True)
    reporter = UserNameSerializer(read_only=True)
    assigner = UserNameSerializer(read_only=True)
    assigned_mediator = UserNameSerializer(read_only=True)

    report_images = serializers.SerializerMethodField()
    report_files = serializers.SerializerMethodField()
    complete_images = serializers.SerializerMethodField()
    complete_files = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "code",
            "task_type",
            "town",
            "status",
            "description",
            "amount",
            "grid",
            "party_name",
            "party_phone",
            "party_address",
            "reporter",
            "reported_at",
            "report_lng",
            "report_lat",
            "report_address",
            "report_images",
            "report_files",
            "assigner",
            "assigned_mediator",
            "assigned_at",
            "process_submitted_at",
            "participants",
            "handle_method",
            "expected_plan",
            "result",
            "result_detail",
            "process_description",
            "completed_at",
            "complete_lng",
            "complete_lat",
            "complete_address",
            "complete_images",
            "complete_files",
            "created_at",
            "updated_at",
        ]

    def _attachments(self, ids_str: str):
        files = get_attachments_by_ids(ids_str)
        result = []
        for f in files:
            file_url = f.get("file", "")
            if file_url:
                file_url = get_absolute_url(file_url)
            result.append({"id": f.get("id"), "file": file_url, "original_name": f.get("original_name")})
        return result

    def get_report_images(self, obj: Task):
        return self._attachments(obj.report_image_ids)

    def get_report_files(self, obj: Task):
        return self._attachments(obj.report_file_ids)

    def get_complete_images(self, obj: Task):
        return self._attachments(obj.complete_image_ids)

    def get_complete_files(self, obj: Task):
        return self._attachments(obj.complete_file_ids)


def _validate_attachment_ids_exist(ids_str: str):
    """校验附件 ID 列表是否存在。"""

    ids = parse_attachment_ids(ids_str)
    if not ids:
        return ids_str

    existing = set(Attachment.objects.filter(id__in=ids).values_list("id", flat=True))
    missing = [i for i in ids if i not in existing]
    if missing:
        raise serializers.ValidationError(f"附件不存在: {','.join(map(str, missing))}")
    return ids_str


class TaskCreateSerializer(serializers.ModelSerializer):
    """上报任务（调解员）。"""

    task_type_id = serializers.IntegerField(write_only=True, required=True)
    town_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Task
        fields = [
            "task_type_id",
            "town_id",
            "description",
            "party_name",
            "party_phone",
            "party_address",
            "amount",
            "report_lng",
            "report_lat",
            "report_address",
            "report_image_ids",
            "report_file_ids",
        ]

    def validate_task_type_id(self, value):
        if not TaskType.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("任务类型不存在或已禁用")
        return value

    def validate_town_id(self, value):
        if value and not Town.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("所属镇不存在或已禁用")
        return value

    def validate_party_name(self, value):
        if not value:
            raise serializers.ValidationError("当事人姓名不能为空")
        return value

    def validate_description(self, value):
        if not value:
            raise serializers.ValidationError("任务描述不能为空")
        return value

    def validate_report_image_ids(self, value):
        return _validate_attachment_ids_exist(value)

    def validate_report_file_ids(self, value):
        return _validate_attachment_ids_exist(value)

    def create(self, validated_data):
        request = self.context.get("request")
        reporter: User = getattr(request, "user", None)

        validated_data["reporter"] = reporter
        validated_data["status"] = Task.Status.REPORTED

        # 根据上报人所属网格自动分配
        if not reporter.grid:
            raise serializers.ValidationError("您尚未分配到任何网格，无法上报任务")
        validated_data["grid"] = reporter.grid

        # 处理外键字段
        task_type_id = validated_data.pop("task_type_id")
        validated_data["task_type_id"] = task_type_id
        
        town_id = validated_data.pop("town_id", None)
        if town_id:
            validated_data["town_id"] = town_id

        # 生成任务编号
        task_type = TaskType.objects.get(id=task_type_id)
        validated_data["code"] = generate_task_code(task_type=task_type.code)

        return Task.objects.create(**validated_data)


class TaskProcessSerializer(serializers.Serializer):
    """提交进行中信息。"""

    participants = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    handle_method = serializers.ChoiceField(choices=Task.HandleMethod.choices, required=True)
    expected_plan = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TaskCompleteSerializer(serializers.Serializer):
    """提交完成结果。"""

    result = serializers.ChoiceField(choices=Task.Result.choices, required=True)
    result_detail = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    process_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    complete_lng = serializers.DecimalField(required=False, max_digits=10, decimal_places=7)
    complete_lat = serializers.DecimalField(required=False, max_digits=10, decimal_places=7)
    complete_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    complete_image_ids = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    complete_file_ids = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")

    def validate_complete_image_ids(self, value):
        return _validate_attachment_ids_exist(value or "")

    def validate_complete_file_ids(self, value):
        return _validate_attachment_ids_exist(value or "")
