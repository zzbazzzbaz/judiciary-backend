"""
Grids 子应用序列化器

说明：
- Grid 创建/更新时会校验 boundary 格式，并在缺省中心点时自动计算中心点。
"""

from __future__ import annotations

from rest_framework import serializers

from utils.geo_utils import calculate_center, validate_boundary

from apps.users.models import User

from .models import Grid, MediatorAssignment


class UserSimpleSerializer(serializers.ModelSerializer):
    """用户简要信息（用于嵌套展示）。"""

    class Meta:
        model = User
        fields = ["id", "name", "phone"]


class GridListSerializer(serializers.ModelSerializer):
    """网格列表项。"""

    current_manager = UserSimpleSerializer(read_only=True)
    mediator_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Grid
        fields = [
            "id",
            "name",
            "region",
            "center_lng",
            "center_lat",
            "current_manager",
            "mediator_count",
            "is_active",
            "created_at",
        ]


class GridDetailSerializer(serializers.ModelSerializer):
    """网格详情。"""

    current_manager = UserSimpleSerializer(read_only=True)
    mediator_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Grid
        fields = [
            "id",
            "name",
            "region",
            "boundary",
            "center_lng",
            "center_lat",
            "current_manager",
            "description",
            "mediator_count",
            "is_active",
            "created_at",
            "updated_at",
        ]


class GridCreateUpdateSerializer(serializers.ModelSerializer):
    """网格创建/更新入参。"""

    current_manager_id = serializers.PrimaryKeyRelatedField(
        source="current_manager",
        queryset=User.objects.filter(role=User.Role.GRID_MANAGER, is_active=True),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Grid
        fields = [
            "id",
            "name",
            "region",
            "boundary",
            "center_lng",
            "center_lat",
            "current_manager_id",
            "description",
            "is_active",
        ]

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("网格名称不能为空")
        return value

    def validate_boundary(self, value):
        if value in (None, ""):
            return None
        if not validate_boundary(value):
            raise serializers.ValidationError("边界坐标格式不正确")
        return value

    def validate(self, attrs):
        # 中心点经纬度需成对出现，避免仅更新一边导致数据异常
        has_lng = "center_lng" in attrs
        has_lat = "center_lat" in attrs
        if has_lng ^ has_lat:
            raise serializers.ValidationError("中心点经纬度需同时提供")
        return attrs

    def _fill_center_if_needed(self, data: dict):
        """
        当提交了 boundary 但未提供中心点时，自动计算中心点。
        """

        if "boundary" not in data:
            return
        boundary = data.get("boundary")
        if not boundary:
            return

        if "center_lng" not in data and "center_lat" not in data:
            center_lng, center_lat = calculate_center(boundary)
            data["center_lng"] = center_lng
            data["center_lat"] = center_lat

    def create(self, validated_data):
        self._fill_center_if_needed(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._fill_center_if_needed(validated_data)
        return super().update(instance, validated_data)


class GridManagerUpdateSerializer(serializers.Serializer):
    """设置/清除网格负责人。"""

    manager_id = serializers.IntegerField(required=True, allow_null=True)


class MediatorAddSerializer(serializers.Serializer):
    """向网格添加调解员。"""

    mediator_id = serializers.IntegerField(required=True)


class MediatorAssignmentSerializer(serializers.ModelSerializer):
    """网格调解员分配记录（内部使用）。"""

    mediator = UserSimpleSerializer(read_only=True)

    class Meta:
        model = MediatorAssignment
        fields = ["id", "mediator", "created_at"]

