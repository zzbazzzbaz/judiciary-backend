"""
自定义 Token 认证后端

替代 JWT Authentication，使用简单 Token + 缓存方案。
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.users.models import User
from utils.token_manager import TokenManager


class SimpleTokenAuthentication(BaseAuthentication):
    """
    简单 Token 认证

    Header 格式: Authorization: Bearer <token>
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return None  # 未提供认证信息，交给权限类处理

        parts = auth_header.split()

        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]

        # 验证 Token
        user_id = TokenManager.verify_access_token(token)
        if not user_id:
            raise AuthenticationFailed("Token 无效或已过期")

        # 获取用户
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise AuthenticationFailed("用户不存在或已被禁用")

        # 将 token 存到 request 中，登出时使用
        request.auth_token = token

        return (user, token)

    def authenticate_header(self, request):
        return self.keyword
