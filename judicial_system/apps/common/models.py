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

        IMAGE = "image", "Image"
        DOCUMENT = "document", "Document"

    file = models.FileField(max_length=255, upload_to="attachments/%Y/%m/")  # 文件路径
    file_type = models.CharField(max_length=20, choices=FileType.choices)  # image/document
    file_size = models.BigIntegerField(null=True, blank=True, default=0)  # 文件大小（字节）
    original_name = models.CharField(max_length=255, null=True, blank=True)  # 原始文件名

    class Meta:
        db_table = "common_attachment"
