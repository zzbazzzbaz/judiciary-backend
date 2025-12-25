"""
Users 子应用序列化器

说明：
- 认证相关序列化器：登录、刷新、修改密码、个人信息。
- 机构管理序列化器：列表。
"""

from __future__ import annotations

from datetime import datetime

from rest_framework import serializers

from utils.url_utils import get_absolute_url
from utils.validators import validate_password_strength, validate_phone

from apps.cases.models import Task
from apps.grids.models import Grid

from .models import Organization, User, PerformanceScore


class OrganizationSimpleSerializer(serializers.ModelSerializer):
    """机构简要信息（用于嵌套展示）。"""

    class Meta:
        model = Organization
        fields = ["id", "name"]


class GridSerializer(serializers.ModelSerializer):
    """网格详细信息序列化器。"""

    # 当前负责人的姓名
    current_manager_name = serializers.CharField(
        source="current_manager.name",
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Grid
        fields = ["id", "name", "region", "description", "current_manager_name"]


class LoginSerializer(serializers.Serializer):
    """登录入参序列化器。"""

    username = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)


class TokenRefreshSerializer(serializers.Serializer):
    """刷新 Token 入参序列化器。"""

    refresh_token = serializers.CharField(required=True, allow_blank=False)


class PasswordChangeSerializer(serializers.Serializer):
    """修改密码入参序列化器。"""

    old_password = serializers.CharField(required=True, allow_blank=False, write_only=True)
    new_password = serializers.CharField(required=True, allow_blank=False, write_only=True)
    confirm_password = serializers.CharField(required=True, allow_blank=False, write_only=True)

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError("两次密码不一致")
        if not validate_password_strength(new_password):
            raise serializers.ValidationError("密码强度不足（至少6位，包含字母和数字）")
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """个人信息更新（仅允许修改 phone）。"""

    class Meta:
        model = User
        fields = ["phone", "avatar"]

    def validate_phone(self, value):
        if value and not validate_phone(value):
            raise serializers.ValidationError("手机号格式不正确")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """个人信息详情。"""

    avatar = serializers.SerializerMethodField()
    organization = OrganizationSimpleSerializer(read_only=True)
    # 使用网格序列化器返回详细信息
    grid = GridSerializer(read_only=True)
    # 本月绩效分数
    monthly_performance = serializers.SerializerMethodField()
    # 本月完成任务数
    monthly_completed_tasks = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
            "gender",
            "id_card",
            "phone",
            "avatar",
            "role",
            "organization",
            "grid",
            "is_active",
            "last_login",
            "created_at",
            "updated_at",
            "monthly_performance",
            "monthly_completed_tasks",
        ]

    def get_avatar(self, obj: User) -> str:
        if not obj.avatar:
            return ""
        try:
            return get_absolute_url(obj.avatar.url)
        except Exception:
            return ""

    def get_monthly_performance(self, obj):
        """获取本月绩效分数。

        Args:
            obj: User 实例

        Returns:
            int: 本月绩效分数，如果没有则返回 None
        """
        # 获取当前年月，格式：YYYY-MM
        current_period = datetime.now().strftime("%Y-%m")

        # 查询本月绩效记录
        performance = PerformanceScore.objects.filter(
            mediator=obj,
            period=current_period
        ).first()

        return performance.score if performance else None

    def get_monthly_completed_tasks(self, obj):
        """获取本月完成任务数。

        Args:
            obj: User 实例

        Returns:
            int: 本月完成的任务数量
        """
        # 获取本月的起始时间
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)

        # 计算下个月的起始时间
        if now.month == 12:
            next_month_start = datetime(now.year + 1, 1, 1)
        else:
            next_month_start = datetime(now.year, now.month + 1, 1)

        # 查询本月完成的任务数量
        count = Task.objects.filter(
            assigned_mediator=obj,
            status=Task.Status.COMPLETED,
            completed_at__gte=month_start,
            completed_at__lt=next_month_start
        ).count()

        return count

class OrganizationListSerializer(serializers.ModelSerializer):
    """机构列表项（扁平结构）。"""

    parent_id = serializers.IntegerField(source="parent.id", read_only=True)
    parent_name = serializers.CharField(source="parent.name", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "parent_id",
            "parent_name",
            "is_active",
            "sort_order",
        ]
