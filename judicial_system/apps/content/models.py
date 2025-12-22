"""
Content 模块模型

模块说明：
- 内容管理：文档资料、法治宣传等文章内容与分类管理。
"""

from django.db import models
from ckeditor.fields import RichTextField


class Category(models.Model):
    """分类表（content_category）。"""

    name = models.CharField("分类名称", max_length=50, unique=True)
    sort_order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "content_category"
        verbose_name = "文章分类"
        verbose_name_plural = verbose_name

    def __str__(self) -> str: return self.name


class Article(models.Model):
    """文章表（content_article）。"""

    class Status(models.TextChoices):
        """状态（draft/published/archived）。"""

        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
        ARCHIVED = "archived", "已归档"

    title = models.CharField("标题", max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="articles", verbose_name="分类")
    content = RichTextField("正文内容", null=True, blank=True)
    cover_image = models.ImageField("封面图片", upload_to="articles/covers/%Y/%m/", null=True, blank=True)
    video = models.FileField("视频", upload_to="articles/videos/%Y/%m/", null=True, blank=True)
    files = models.ManyToManyField(
        "ContentAttachment",
        blank=True,
        verbose_name="文章附件",
    )
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.DRAFT)
    sort_order = models.IntegerField("排序", default=0)
    publisher = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="published_articles",
        verbose_name="发布人",
    )
    published_at = models.DateTimeField("发布时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "content_article"
        verbose_name = "文章"
        verbose_name_plural = verbose_name

    def __str__(self) -> str: return self.title


class Activity(models.Model):
    """活动表（content_activity）。"""

    name = models.CharField("活动名称", max_length=200)
    start_time = models.DateTimeField("开始时间")
    registration_start = models.DateTimeField("报名开始时间")
    registration_end = models.DateTimeField("报名结束时间")
    content = RichTextField("活动内容", null=True, blank=True)
    files = models.ManyToManyField(
        "ContentAttachment",
        blank=True,
        verbose_name="活动附件",
    )
    participants = models.ManyToManyField("users.User", blank=True, related_name="activities", verbose_name="报名列表")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "content_activity"
        verbose_name = "活动"
        verbose_name_plural = verbose_name


class ContentAttachment(models.Model):
    file = models.FileField("文件", max_length=255, upload_to="content/%Y/%m/")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "content_attachment"
        verbose_name = "附件"
        verbose_name_plural = verbose_name

    def __str__(self) -> str: return self.file.name.split("/")[-1]


####################################################################################################

class DocumentCategory(models.Model):
    """文档分类表（content_document_category）。"""

    name = models.CharField("分类名称", max_length=50, unique=True)
    sort_order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "content_document_category"
        verbose_name = "文档分类"
        verbose_name_plural = verbose_name

    def __str__(self) -> str: return self.name


class Document(models.Model):
    """文档资料表（content_document）。"""

    name = models.CharField("文档名称", max_length=200)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name="分类",
        null=True,
        blank=True,
    )
    file = models.FileField("文件", max_length=255, upload_to="documents/%Y/%m/")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "content_document"
        verbose_name = "文档资料"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.file.name.split("/")[-1]
