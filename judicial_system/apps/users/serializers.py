"""
Users 子应用序列化器

说明：
- 认证相关序列化器：登录、刷新、修改密码、个人信息。
- 管理端用户管理序列化器：列表/详情/创建/更新。
"""

from __future__ import annotations

from rest_framework import serializers

from utils.validators import validate_id_card, validate_password_strength, validate_phone, validate_username

from .models import Organization, PerformanceScore, User


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


class UserListSerializer(serializers.ModelSerializer):
    """用户列表项。"""

    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
            "gender",
            "phone",
            "role",
            "organization_name",
            "is_active",
            "created_at",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详情（管理端）。"""

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


class UserCreateSerializer(serializers.ModelSerializer):
    """新增用户（管理端）。"""

    password = serializers.CharField(write_only=True, required=True, allow_blank=False)
    organization_id = serializers.PrimaryKeyRelatedField(
        source="organization",
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "name",
            "gender",
            "id_card",
            "phone",
            "organization_id",
            "role",
            "is_active",
        ]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        if not validate_username(value):
            raise serializers.ValidationError("用户名格式不正确（字母数字下划线，4-20位）")
        return value

    def validate_password(self, value):
        if not validate_password_strength(value):
            raise serializers.ValidationError("密码强度不足（至少6位，包含字母和数字）")
        return value

    def validate_id_card(self, value):
        if value and not validate_id_card(value):
            raise serializers.ValidationError("身份证号格式不正确")
        return value

    def validate_phone(self, value):
        if value and not validate_phone(value):
            raise serializers.ValidationError("手机号格式不正确")
        return value

    def create(self, validated_data):
        # 使用自定义用户管理器创建用户，保证密码加密存储
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """更新用户（管理端）。"""

    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    organization_id = serializers.PrimaryKeyRelatedField(
        source="organization",
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            "name",
            "gender",
            "id_card",
            "phone",
            "organization_id",
            "role",
            "is_active",
            "password",
        ]

    def validate_password(self, value):
        if value and not validate_password_strength(value):
            raise serializers.ValidationError("密码强度不足（至少6位，包含字母和数字）")
        return value

    def validate_id_card(self, value):
        if value and not validate_id_card(value):
            raise serializers.ValidationError("身份证号格式不正确")
        return value

    def validate_phone(self, value):
        if value and not validate_phone(value):
            raise serializers.ValidationError("手机号格式不正确")
        return value

    def update(self, instance: User, validated_data):
        # password 需要走 set_password 进行哈希
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


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


class OrganizationCreateUpdateSerializer(serializers.ModelSerializer):
    """机构创建/更新。"""

    parent_id = serializers.PrimaryKeyRelatedField(
        source="parent",
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "parent_id",
            "description",
            "contact",
            "address",
            "sort_order",
            "is_active",
        ]

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("机构名称不能为空")
        return value

    def validate(self, attrs):
        """
        parent 循环引用校验：
        - 不能将自己设为父级
        - 不能形成循环（父级不能是自己的子孙节点）
        """

        parent = attrs.get("parent")
        instance: Organization | None = getattr(self, "instance", None)
        if not instance or not parent:
            return attrs

        if parent.id == instance.id:
            raise serializers.ValidationError("不能将自己设为父级")

        # 从 parent 往上追溯，若遇到 instance 则形成循环
        cursor = parent
        while cursor:
            if cursor.id == instance.id:
                raise serializers.ValidationError("不能形成循环引用")
            cursor = cursor.parent

        return attrs


class PerformanceScoreSerializer(serializers.ModelSerializer):
    """绩效打分记录输出。"""

    mediator_id = serializers.IntegerField(source="mediator.id", read_only=True)
    mediator_name = serializers.CharField(source="mediator.name", read_only=True)
    scorer_id = serializers.IntegerField(source="scorer.id", read_only=True)
    scorer_name = serializers.CharField(source="scorer.name", read_only=True)

    class Meta:
        model = PerformanceScore
        fields = [
            "id",
            "mediator_id",
            "mediator_name",
            "scorer_id",
            "scorer_name",
            "score",
            "period",
            "comment",
            "created_at",
        ]


class PerformanceScoreUpsertSerializer(serializers.Serializer):
    """绩效打分入参（创建或更新）。"""

    mediator_id = serializers.IntegerField(required=True)
    score = serializers.IntegerField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("分数必须在 0-100 之间")
        return value
