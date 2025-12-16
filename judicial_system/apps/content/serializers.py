# """
# Content 子应用序列化器
#
# 包含：
# - 分类（Category）列表
# - 文章（Article）管理端：列表/详情/创建/更新
# - 文章（Article）移动端：已发布列表/详情
# """
#
# from __future__ import annotations
#
# from rest_framework import serializers
#
# from utils.attachment_utils import get_attachments_by_ids, parse_attachment_ids
#
# from apps.common.models import Attachment
# from apps.users.models import User
#
# from .models import Article, Category
#
#
# class CategorySerializer(serializers.ModelSerializer):
#     """分类输出（列表用）。"""
#
#     class Meta:
#         model = Category
#         fields = ["id", "name", "sort_order"]
#
#
# class CategorySimpleSerializer(serializers.ModelSerializer):
#     """分类简要信息（详情嵌套展示）。"""
#
#     class Meta:
#         model = Category
#         fields = ["id", "name"]
#
#
# class UserNameSerializer(serializers.ModelSerializer):
#     """用户简要信息（id/name）。"""
#
#     class Meta:
#         model = User
#         fields = ["id", "name"]
#
#
# def _validate_attachment_ids_exist(ids_str: str):
#     """校验附件 ID 列表是否存在。"""
#
#     ids = parse_attachment_ids(ids_str)
#     if not ids:
#         return ids_str
#
#     existing = set(Attachment.objects.filter(id__in=ids).values_list("id", flat=True))
#     missing = [i for i in ids if i not in existing]
#     if missing:
#         raise serializers.ValidationError(f"附件不存在: {','.join(map(str, missing))}")
#     return ids_str
#
#
# class ArticleListSerializer(serializers.ModelSerializer):
#     """文章列表项（管理端）。"""
#
#     category_id = serializers.IntegerField(source="category.id", read_only=True)
#     category_name = serializers.CharField(source="category.name", read_only=True)
#     publisher_name = serializers.CharField(source="publisher.name", read_only=True)
#
#     class Meta:
#         model = Article
#         fields = [
#             "id",
#             "title",
#             "category_id",
#             "category_name",
#             "status",
#             "publisher_name",
#             "published_at",
#             "created_at",
#         ]
#
#
# class ArticleDetailSerializer(serializers.ModelSerializer):
#     """文章详情（管理端）。"""
#
#     category = CategorySimpleSerializer(read_only=True)
#     publisher = UserNameSerializer(read_only=True)
#     files = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Article
#         fields = [
#             "id",
#             "title",
#             "category",
#             "content",
#             "cover_image",
#             "video",
#             "files",
#             "status",
#             "sort_order",
#             "publisher",
#             "published_at",
#             "created_at",
#             "updated_at",
#         ]
#
#     def get_files(self, obj: Article):
#         return get_attachments_by_ids(obj.file_ids)
#
#
# class ArticleCreateSerializer(serializers.ModelSerializer):
#     """创建文章（管理端，默认草稿）。"""
#
#     category_id = serializers.PrimaryKeyRelatedField(
#         source="category",
#         queryset=Category.objects.all(),
#         write_only=True,
#         required=True,
#     )
#
#     class Meta:
#         model = Article
#         fields = ["id", "title", "category_id", "content", "cover_image", "video", "file_ids", "sort_order", "status", "created_at"]
#         read_only_fields = ["id", "status", "created_at"]
#
#     def validate_title(self, value):
#         if not value:
#             raise serializers.ValidationError("标题不能为空")
#         return value
#
#     def validate_file_ids(self, value):
#         return _validate_attachment_ids_exist(value or "")
#
#
# class ArticleUpdateSerializer(serializers.ModelSerializer):
#     """更新文章（管理端）。"""
#
#     category_id = serializers.PrimaryKeyRelatedField(
#         source="category",
#         queryset=Category.objects.all(),
#         write_only=True,
#         required=False,
#     )
#
#     class Meta:
#         model = Article
#         fields = ["title", "category_id", "content", "cover_image", "video", "file_ids", "sort_order"]
#
#     def validate_title(self, value):
#         if value is not None and value == "":
#             raise serializers.ValidationError("标题不能为空")
#         return value
#
#     def validate_file_ids(self, value):
#         return _validate_attachment_ids_exist(value or "")
#
#
# class ArticlePublishedListSerializer(serializers.ModelSerializer):
#     """已发布文章列表（移动端）。"""
#
#     category_name = serializers.CharField(source="category.name", read_only=True)
#
#     class Meta:
#         model = Article
#         fields = ["id", "title", "category_name", "cover_image", "published_at"]
#
#
# class ArticlePublishedDetailSerializer(serializers.ModelSerializer):
#     """已发布文章详情（移动端）。"""
#
#     category_name = serializers.CharField(source="category.name", read_only=True)
#     files = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Article
#         fields = ["id", "title", "category_name", "content", "cover_image", "video", "files", "published_at"]
#
#     def get_files(self, obj: Article):
#         return get_attachments_by_ids(obj.file_ids)
