"""
Common 模块模型

说明：
- 附件表仅存储文件元信息；业务表通过 *_ids 字段（逗号分隔的ID列表）进行关联。
"""

from django.db import models


class Attachment(models.Model):
    """通用附件表（common_attachment）。"""

    class FileType(models.TextChoices):
        """文件类型。"""

        IMAGE = "image", "图片"
        DOCUMENT = "document", "文档"

    file = models.FileField("文件", max_length=255, upload_to="attachments/%Y/%m/")
    file_type = models.CharField("文件类型", max_length=20, choices=FileType.choices)
    file_size = models.BigIntegerField("文件大小", null=True, blank=True, default=0)
    original_name = models.CharField("原始文件名", max_length=255, null=True, blank=True)

    class Meta:
        db_table = "common_attachment"
        verbose_name = "附件"
        verbose_name_plural = verbose_name

class MapConfig(models.Model):
    """地图配置表（common_map_config）。"""

    zoom_level = models.IntegerField("缩放级别(3-20)", default=12)
    center_longitude = models.DecimalField("中心点经度", max_digits=10, decimal_places=7)
    center_latitude = models.DecimalField("中心点纬度", max_digits=10, decimal_places=7)
    api_key = models.CharField("API密钥", max_length=255, blank=True, default="")
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "common_map_config"
        verbose_name = "地图配置"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"地图配置 (缩放: {self.zoom_level}, 中心: {self.center_longitude}, {self.center_latitude})"