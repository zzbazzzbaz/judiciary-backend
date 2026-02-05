"""
简单 Token 管理器

使用 Django Cache 存储 Token，替代 JWT。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from django.core.cache import cache


class TokenManager:
    """Token 管理器"""

    # Token 前缀
    ACCESS_TOKEN_PREFIX = "auth_token:"
    REFRESH_TOKEN_PREFIX = "refresh_token:"
    USER_TOKEN_PREFIX = "user_tokens:"  # 用户 -> token 映射（单点登录）

    # 过期时间（秒）
    ACCESS_TOKEN_LIFETIME = 2 * 60 * 60  # 2小时
    REFRESH_TOKEN_LIFETIME = 7 * 24 * 60 * 60  # 7天

    @classmethod
    def generate_token(cls) -> str:
        """生成随机 Token"""
        return uuid.uuid4().hex

    @classmethod
    def create_tokens(cls, user_id: int) -> Dict[str, Any]:
        """
        为用户创建 access_token 和 refresh_token
        单点登录：新登录会撤销该用户的旧 Token

        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 7200
            }
        """
        # 单点登录：先撤销该用户的旧 Token
        cls.revoke_user_tokens(user_id)

        access_token = cls.generate_token()
        refresh_token = cls.generate_token()

        now = datetime.now()

        # 存储 access_token
        access_data = {
            "user_id": user_id,
            "created_at": now.isoformat(),
            "token_type": "access",
        }
        cache.set(
            f"{cls.ACCESS_TOKEN_PREFIX}{access_token}",
            access_data,
            timeout=cls.ACCESS_TOKEN_LIFETIME,
        )

        # 存储 refresh_token (关联 access_token)
        refresh_data = {
            "user_id": user_id,
            "created_at": now.isoformat(),
            "token_type": "refresh",
            "access_token": access_token,
        }
        cache.set(
            f"{cls.REFRESH_TOKEN_PREFIX}{refresh_token}",
            refresh_data,
            timeout=cls.REFRESH_TOKEN_LIFETIME,
        )

        # 保存用户 -> token 映射
        cache.set(
            f"{cls.USER_TOKEN_PREFIX}{user_id}",
            {"access_token": access_token, "refresh_token": refresh_token},
            timeout=cls.REFRESH_TOKEN_LIFETIME,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": cls.ACCESS_TOKEN_LIFETIME,
        }

    @classmethod
    def verify_access_token(cls, token: str) -> Optional[int]:
        """
        验证 access_token

        Returns:
            user_id 或 None（无效/过期）
        """
        data = cache.get(f"{cls.ACCESS_TOKEN_PREFIX}{token}")
        if data and data.get("token_type") == "access":
            return data.get("user_id")
        return None

    @classmethod
    def verify_refresh_token(cls, token: str) -> Optional[int]:
        """
        验证 refresh_token

        Returns:
            user_id 或 None（无效/过期）
        """
        data = cache.get(f"{cls.REFRESH_TOKEN_PREFIX}{token}")
        if data and data.get("token_type") == "refresh":
            return data.get("user_id")
        return None

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        使用 refresh_token 刷新 access_token

        Returns:
            新的 token 信息 或 None
        """
        user_id = cls.verify_refresh_token(refresh_token)
        if not user_id:
            return None

        # 获取旧的 refresh_data
        refresh_data = cache.get(f"{cls.REFRESH_TOKEN_PREFIX}{refresh_token}")
        old_access_token = refresh_data.get("access_token") if refresh_data else None

        # 删除旧的 access_token
        if old_access_token:
            cache.delete(f"{cls.ACCESS_TOKEN_PREFIX}{old_access_token}")

        # 生成新的 access_token
        new_access_token = cls.generate_token()
        now = datetime.now()

        access_data = {
            "user_id": user_id,
            "created_at": now.isoformat(),
            "token_type": "access",
        }
        cache.set(
            f"{cls.ACCESS_TOKEN_PREFIX}{new_access_token}",
            access_data,
            timeout=cls.ACCESS_TOKEN_LIFETIME,
        )

        # 更新 refresh_data 中的 access_token 引用
        if refresh_data:
            refresh_data["access_token"] = new_access_token
            cache.set(
                f"{cls.REFRESH_TOKEN_PREFIX}{refresh_token}",
                refresh_data,
                timeout=cls.REFRESH_TOKEN_LIFETIME,
            )

        return {
            "access_token": new_access_token,
            "expires_in": cls.ACCESS_TOKEN_LIFETIME,
        }

    @classmethod
    def revoke_token(cls, access_token: str) -> bool:
        """撤销 access_token（登出时调用）"""
        # 获取 user_id 以清理用户映射
        data = cache.get(f"{cls.ACCESS_TOKEN_PREFIX}{access_token}")
        if data:
            user_id = data.get("user_id")
            if user_id:
                cache.delete(f"{cls.USER_TOKEN_PREFIX}{user_id}")
        cache.delete(f"{cls.ACCESS_TOKEN_PREFIX}{access_token}")
        return True

    @classmethod
    def revoke_user_tokens(cls, user_id: int) -> bool:
        """撤销用户所有 Token（单点登录时调用）"""
        token_mapping = cache.get(f"{cls.USER_TOKEN_PREFIX}{user_id}")
        if token_mapping:
            access_token = token_mapping.get("access_token")
            refresh_token = token_mapping.get("refresh_token")
            if access_token:
                cache.delete(f"{cls.ACCESS_TOKEN_PREFIX}{access_token}")
            if refresh_token:
                cache.delete(f"{cls.REFRESH_TOKEN_PREFIX}{refresh_token}")
            cache.delete(f"{cls.USER_TOKEN_PREFIX}{user_id}")
        return True
