"""
Users 子应用序列化器

说明：
- 认证相关序列化器：登录、刷新、修改密码、个人信息。
- 机构管理序列化器：列表。
"""

from __future__ import annotations

from rest_framework import serializers

from utils.validators import validate_password_strength, validate_phone

from .models import Organization, User


class OrganizationSimpleSerializer(serializers.ModelSerializer):
    """机构简要信息（用于嵌套展示）。"""

    class Meta:
        model = Organization
        fields = ["id", "name"]


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
        fields = ["phone"]

    def validate_phone(self, value):
        if value and not validate_phone(value):
            raise serializers.ValidationError("手机号格式不正确")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """个人信息详情。"""

    organization = OrganizationSimpleSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
            "gender",
            "id_card",
            "phone",
            "role",
            "organization",
            "is_active",
            "last_login",
            "created_at",
            "updated_at",
        ]

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
