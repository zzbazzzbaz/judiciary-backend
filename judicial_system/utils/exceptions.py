"""
DRF 全局异常处理

用于将 DRF 默认错误响应统一包装为：
{ "code": http_status, "message": "...", "data": ... }
"""

from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def _extract_first_error_message(detail: Any) -> str:
    """从 DRF 的错误 detail 中提取第一条可读信息。"""

    if detail is None:
        return "请求参数错误"

    if isinstance(detail, str):
        return detail

    if isinstance(detail, list) and detail:
        return _extract_first_error_message(detail[0])

    if isinstance(detail, dict):
        # 常见结构：{"field": ["msg"]} 或 {"detail": "msg"}
        if "detail" in detail:
            return _extract_first_error_message(detail.get("detail"))
        for _, v in detail.items():
            return _extract_first_error_message(v)

    return "请求参数错误"


def custom_exception_handler(exc, context):
    """
    统一异常输出格式。

    注意：仅做格式包装；具体错误码仍遵循 DRF 的 HTTP 状态码语义。
    """

    response = exception_handler(exc, context)
    if response is None:
        return Response({"code": 500, "message": "服务器内部错误"}, status=500)

    message = _extract_first_error_message(response.data)
    payload = {"code": response.status_code, "message": message}

    # 需要时可携带原始错误详情，便于前端做字段级提示
    if isinstance(response.data, (dict, list)):
        payload["data"] = response.data

    response.data = payload
    return response

