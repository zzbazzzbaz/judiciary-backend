"""
Content 模块模型

模块说明：
- 内容管理：文档资料、法治宣传等文章内容与分类管理。
"""

from django.db import models


class Category(models.Model):
    """分类表（content_category）。"""

    code = models.CharField(max_length=50, unique=True)  # 分类编码（唯一，如 law_doc/policy/template）
    name = models.CharField(max_length=50)  # 分类名称
    is_template = models.BooleanField(default=False)  # 是否文书模板分类
    sort_order = models.IntegerField(default=0)  # 排序
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间

    class Meta:
        db_table = "content_category"

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Article(models.Model):
    """文章表（content_article）。"""

    class Status(models.TextChoices):
        """状态（draft/published/archived）。"""

        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=200)  # 标题
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="articles")  # 分类
    content = models.TextField(null=True, blank=True)  # 正文内容（可配合富文本）
    cover_image = models.CharField(max_length=255, null=True, blank=True)  # 封面图片路径
    video = models.CharField(max_length=255, null=True, blank=True)  # 视频路径
    file_ids = models.CharField(  # 附件ID列表（common_attachment.id，逗号分隔）
        max_length=500,
        blank=True,
        default="",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)  # 状态
    sort_order = models.IntegerField(default=0)  # 排序
    view_count = models.IntegerField(default=0)  # 浏览次数
    publisher = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="published_articles",
    )  # 发布人
    published_at = models.DateTimeField(null=True, blank=True)  # 发布时间
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated_at = models.DateTimeField(auto_now=True)  # 更新时间

    class Meta:
        db_table = "content_article"

    def __str__(self) -> str:  # pragma: no cover
        return self.title
