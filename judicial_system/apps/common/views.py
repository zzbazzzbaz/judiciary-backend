"""
Common 子应用 API 视图

接口：
- POST /api/v1/common/upload/            通用文件上传
- GET  /api/v1/common/map-config/        地图配置（当前启用）
"""

from __future__ import annotations

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.file_utils import (
    MAX_FILE_SIZE,
    get_file_extension,
    get_file_type,
    generate_upload_path,
    validate_file_extension,
    validate_file_size,
)
from utils.responses import error_response, success_response

from .models import Attachment, MapConfig
from .serializers import AttachmentSerializer, MapConfigSerializer


class UploadView(APIView):
    """
    通用文件上传。

    说明：
    - 仅登录用户可用（由 JWT 认证/权限控制）。
    - 文件保存到 `media/attachments/年/月/随机文件名.扩展名`。
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return error_response("未选择文件", http_status=400)

        # 1) 校验文件大小（默认 20MB，可通过 MAX_FILE_SIZE 统一配置）
        if not validate_file_size(uploaded_file.size, max_size=MAX_FILE_SIZE):
            return error_response("文件大小超出限制（最大 20MB）", http_status=400)

        # 2) 校验文件扩展名白名单
        extension = get_file_extension(uploaded_file.name)
        if not validate_file_extension(extension):
            return error_response("不支持的文件格式", http_status=400)

        # 3) 推断文件类型（image/document）
        file_type = get_file_type(extension)

        # 4) 保存文件并创建附件记录
        #    这里手动生成上传路径，避免原始文件名冲突并满足「随机文件名」要求。
        upload_path = generate_upload_path(uploaded_file.name)
        from django.core.files.storage import default_storage

        saved_path = default_storage.save(upload_path, uploaded_file)
        attachment = Attachment.objects.create(
            file=saved_path,
            file_type=file_type,
            file_size=uploaded_file.size,
            original_name=uploaded_file.name,
        )

        return success_response(
            data=AttachmentSerializer(attachment, context={"request": request}).data,
            message="上传成功",
        )


class MapConfigAPIView(APIView):
    """获取当前启用的地图配置。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        config = MapConfig.objects.filter(is_active=True).order_by("-updated_at", "-id").first()
        if not config:
            return error_response("地图配置不存在", code=404, http_status=404)
        return success_response(data=MapConfigSerializer(config).data)
