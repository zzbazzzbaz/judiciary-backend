"""
Content 子应用序列化器

接口覆盖：
- 文章：列表/详情
- 活动：列表/详情、报名
"""

from __future__ import annotations

from rest_framework import serializers

from apps.users.models import User

from .models import Activity, Article, Category, ContentAttachment


class ContentAttachmentSerializer(serializers.ModelSerializer):
    """内容附件（file URL + 文件名）。"""

    file = serializers.SerializerMethodField()

    class Meta:
        model = ContentAttachment
        fields = ["id", "file"]

    def get_file(self, obj: ContentAttachment) -> str:
        if not obj.file:
            return ""
        try:
            return obj.file.url
        except Exception:
            return ""


class ArticleListSerializer(serializers.ModelSerializer):
    """文章列表项（不返回正文）。"""

    category_id = serializers.IntegerField(source="category.id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "category_id",
            "category_name",
            "cover_image",
            "published_at",
        ]

    def get_cover_image(self, obj: Article) -> str:
        if not obj.cover_image:
            return ""
        try:
            return obj.cover_image.url
        except Exception:
            return ""


class ArticleDetailSerializer(serializers.ModelSerializer):
    """文章详情（包含正文/附件）。"""

    category_id = serializers.IntegerField(source="category.id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    publisher_id = serializers.IntegerField(source="publisher.id", read_only=True, allow_null=True)
    publisher_name = serializers.CharField(source="publisher.name", read_only=True, allow_null=True)
    cover_image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    files = ContentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "category_id",
            "category_name",
            "content",
            "cover_image",
            "video",
            "files",
            "status",
            "sort_order",
            "publisher_id",
            "publisher_name",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def get_cover_image(self, obj: Article) -> str:
        if not obj.cover_image:
            return ""
        try:
            return obj.cover_image.url
        except Exception:
            return ""

    def get_video(self, obj: Article) -> str:
        if not obj.video:
            return ""
        try:
            return obj.video.url
        except Exception:
            return ""


class UserSimpleSerializer(serializers.ModelSerializer):
    """用户简要信息（id/name）。"""

    class Meta:
        model = User
        fields = ["id", "name"]


class ActivityListSerializer(serializers.ModelSerializer):
    """活动列表项。"""

    participant_count = serializers.IntegerField(read_only=True)
    is_joined = serializers.BooleanField(read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id",
            "name",
            "start_time",
            "registration_start",
            "registration_end",
            "participant_count",
            "is_joined",
            "created_at",
        ]


class ActivityDetailSerializer(serializers.ModelSerializer):
    """活动详情。"""

    files = ContentAttachmentSerializer(many=True, read_only=True)
    participant_count = serializers.IntegerField(read_only=True)
    is_joined = serializers.BooleanField(read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id",
            "name",
            "start_time",
            "registration_start",
            "registration_end",
            "content",
            "files",
            "participant_count",
            "is_joined",
            "created_at",
        ]


class CategorySerializer(serializers.ModelSerializer):
    """文章分类。"""

    class Meta:
        model = Category
        fields = ["id", "name", "sort_order", "created_at"]
