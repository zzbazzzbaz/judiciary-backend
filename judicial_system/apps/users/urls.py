"""Users 子应用路由。"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views.auth import LoginAPIView, LogoutAPIView, PasswordChangeAPIView, ProfileAPIView, TokenRefreshAPIView
from .views.organization import OrganizationViewSet
from .views.performance import PerformanceUserDetailAPIView

router = SimpleRouter()
router.register(r"organizations", OrganizationViewSet, basename="organizations")

urlpatterns = [
    # 认证相关
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("auth/refresh/", TokenRefreshAPIView.as_view(), name="auth-refresh"),
    path("auth/password/change/", PasswordChangeAPIView.as_view(), name="auth-password-change"),
    path("auth/profile/", ProfileAPIView.as_view(), name="auth-profile"),
    # 获取当前用户绩效
    path(
        "performance/my/",
        PerformanceUserDetailAPIView.as_view(),
        name="performance-user-detail",
    ),
    # 业务路由
    path("", include(router.urls)),
]
