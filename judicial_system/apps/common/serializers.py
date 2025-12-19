"""
Common 子应用序列化器

说明：
- 包含：
  - 附件（Attachment）相关序列化器
  - 地图配置（MapConfig）序列化器
"""

from rest_framework import serializers

from utils.url_utils import get_absolute_url

from .models import Attachment, MapConfig


class AttachmentSerializer(serializers.ModelSerializer):
    """附件序列化器。"""

    file = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ["id", "file", "file_type", "file_size", "original_name"]

    def get_file(self, obj: Attachment) -> str:
        """返回文件访问 URL（绝对路径）。"""
        if not obj.file:
            return ""
        try:
            return get_absolute_url(obj.file.url)
        except Exception:
            # 文件可能不存在或存储异常时，避免接口直接 500
            return ""

    def get_file_size(self, obj: Attachment) -> str:
        """返回格式化的文件大小（如 1.5MB 或 500KB）。"""
        if not obj.file_size:
            return "0KB"
        size_bytes = obj.file_size
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        return f"{size_bytes / 1024:.1f}KB"


class MapConfigSerializer(serializers.ModelSerializer):
    """地图配置序列化器。"""

    class Meta:
        model = MapConfig
        fields = [
            "id",
            "zoom_level",
            "center_longitude",
            "center_latitude",
            "api_key",
        ]
