"""
认证相关 API

接口：
- POST /api/v1/auth/login/
- POST /api/v1/auth/logout/
- POST /api/v1/auth/refresh/
- POST /api/v1/auth/password/change/
- GET  /api/v1/auth/profile/
- PUT  /api/v1/auth/profile/
"""

from __future__ import annotations

from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from utils.responses import error_response, success_response
from utils.token_manager import TokenManager
from utils.url_utils import get_absolute_url

from ..models import User
from ..serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
    TokenRefreshSerializer,
    UserProfileSerializer,
)


class LoginAPIView(APIView):
    """用户名密码登录，返回 JWT Token。"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(username=username).select_related("organization").first()
        if not user or not user.check_password(password):
            return error_response("用户名或密码错误", code=401, http_status=401)

        if not user.is_active:
            return error_response("账号已被禁用", code=403, http_status=403)

        # 生成 Token
        tokens = TokenManager.create_tokens(user.id)

        # 记录最后登录时间，便于管理端追踪
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return success_response(
            message="登录成功",
            data={
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "expires_in": tokens["expires_in"],
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "role": user.role,
                    "organization_name": user.organization.name if user.organization else None,
                },
            },
        )


class LogoutAPIView(APIView):
    """用户登出（撤销 Token）。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 获取当前 Token 并撤销
        token = getattr(request, "auth_token", None)
        if token:
            TokenManager.revoke_token(token)

        return success_response(message="登出成功")


class TokenRefreshAPIView(APIView):
    """使用 refresh_token 获取新的 access_token。"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh_token"]

        # 刷新 Token
        result = TokenManager.refresh_access_token(refresh_token)
        if not result:
            return error_response("refresh_token 无效或已过期", code=401, http_status=401)

        return success_response(
            message="刷新成功",
            data={
                "access_token": result["access_token"],
                "expires_in": result["expires_in"],
            },
        )


class PasswordChangeAPIView(APIView):
    """修改当前登录用户密码。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return error_response("原密码错误", http_status=400)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return success_response(message="密码修改成功")


class ProfileAPIView(APIView):
    """个人信息：查询与更新。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return success_response(data=UserProfileSerializer(request.user).data)

    def put(self, request, *args, **kwargs):
        # 需求：仅允许修改 phone
        serializer = ProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # 保存并获取更新后的用户对象

        if getattr(user, "avatar", None):
            try:
                avatar = get_absolute_url(user.avatar.url) if user.avatar else ""
            except Exception:
                avatar = ""
        else:
            avatar = ""

        return success_response(
            message="更新成功",
            data={"id": user.id, "phone": user.phone, "avatar": avatar},  # 返回修改后的手机号
        )

    def post(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

