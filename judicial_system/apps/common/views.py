"""
Common 子应用 API 视图

接口：
- POST /api/v1/common/upload/            通用文件上传
- GET  /api/v1/common/reverse-geocode/   逆地址解析（腾讯地图）
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
from utils.tencent_map import reverse_geocode

from .models import Attachment
from .serializers import AttachmentSerializer


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


class ReverseGeocodeView(APIView):
    """逆地址解析（坐标转地址）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")

        if lat is None or lng is None:
            return error_response("缺少必要参数 lat 或 lng", http_status=400)

        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except (TypeError, ValueError):
            return error_response("lat 或 lng 参数格式不正确", http_status=400)

        # 需求文档约束：中国境内坐标范围校验
        if not (3.86 <= lat_f <= 53.55) or not (73.66 <= lng_f <= 135.05):
            return error_response("坐标超出有效范围", http_status=400)

        try:
            data = reverse_geocode(lat=lat_f, lng=lng_f)
        except Exception:
            # 外部服务调用失败时统一返回 500，避免泄漏异常细节
            return error_response("腾讯地图 API 调用失败", http_status=500)

        if not data:
            return error_response("腾讯地图 API 调用失败", http_status=500)

        return success_response(data=data, message="success")

