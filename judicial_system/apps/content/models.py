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
    files = models.ManyToManyField(
        "ContentAttachment",
        blank=True,
        verbose_name="文章附件",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)  # 状态
    sort_order = models.IntegerField(default=0)  # 排序
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

class ContentAttachment(models.Model):

    file = models.FileField("文件", max_length=255, upload_to="users/%Y/%m/")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "content_attachment"
        verbose_name = "附件"
        verbose_name_plural = verbose_name


class Activity(models.Model):
    """活动表（content_activity）。"""

    name = models.CharField("活动名称", max_length=200)
    start_time = models.DateTimeField("开始时间")
    registration_start = models.DateTimeField("报名开始时间")
    registration_end = models.DateTimeField("报名结束时间")
    content = models.TextField("活动内容", null=True, blank=True)
    participants = models.ManyToManyField("users.User", blank=True, related_name="activities", verbose_name="报名列表")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "content_activity"
        verbose_name = "活动"
        verbose_name_plural = verbose_name


class Document(models.Model):
    """文档资料表（content_document）。"""

    name = models.CharField("文档名称", max_length=200)
    file = models.FileField("文件", max_length=255, upload_to="documents/%Y/%m/")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "content_document"
        verbose_name = "文档资料"
        verbose_name_plural = verbose_name
