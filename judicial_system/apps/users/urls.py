"""Users 子应用路由。"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.auth import LoginAPIView, LogoutAPIView, PasswordChangeAPIView, ProfileAPIView, TokenRefreshAPIView
from .views.organization import OrganizationViewSet
from .views.performance import (
    PerformanceScoreListCreateAPIView,
    PerformanceStatisticsAPIView,
    PerformanceUserDetailAPIView,
)
from .views.training import TrainingRecordDetailAPIView, UserTrainingRecordAPIView
from .views.user import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"organizations", OrganizationViewSet, basename="organizations")

urlpatterns = [
    # 认证相关
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="auth-logout"),
    path("auth/refresh/", TokenRefreshAPIView.as_view(), name="auth-refresh"),
    path("auth/password/change/", PasswordChangeAPIView.as_view(), name="auth-password-change"),
    path("auth/profile/", ProfileAPIView.as_view(), name="auth-profile"),
    # 培训记录
    path("users/<int:user_id>/trainings/", UserTrainingRecordAPIView.as_view(), name="user-trainings"),
    path("trainings/<int:pk>/", TrainingRecordDetailAPIView.as_view(), name="training-detail"),
    # 绩效管理
    path(
        "performance/scores/",
        PerformanceScoreListCreateAPIView.as_view(),
        name="performance-scores",
    ),
    path(
        "performance/statistics/",
        PerformanceStatisticsAPIView.as_view(),
        name="performance-statistics",
    ),
    path(
        "performance/user/<int:user_id>/",
        PerformanceUserDetailAPIView.as_view(),
        name="performance-user-detail",
    ),
    # 业务路由
    path("", include(router.urls)),
]
