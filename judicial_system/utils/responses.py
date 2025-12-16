"""统一 API 响应封装。"""

from __future__ import annotations

from typing import Any

from rest_framework.response import Response


def success_response(*, data: Any = None, message: str = "success", code: int = 200, http_status: int = 200):
    """成功响应。"""

    payload: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=http_status)


def error_response(message: str, *, code: int = 400, http_status: int = 400, data: Any = None):
    """错误响应。"""

    payload: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=http_status)

