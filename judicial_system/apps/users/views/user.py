"""用户管理 API（管理端）。"""

from __future__ import annotations

from django.db.models import Q
from rest_framework import status, viewsets

from utils.pagination import StandardPageNumberPagination
from utils.permissions import IsAdmin
from utils.responses import error_response, success_response
from utils.validators import parse_bool

from ..models import User
from ..serializers import UserCreateSerializer, UserDetailSerializer, UserListSerializer, UserUpdateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理（管理员）：
    - GET    /api/v1/users/
    - POST   /api/v1/users/
    - GET    /api/v1/users/{id}/
    - PUT    /api/v1/users/{id}/
    - DELETE /api/v1/users/{id}/   软删除（is_active=False）
    """

    permission_classes = [IsAdmin]
    pagination_class = StandardPageNumberPagination
    queryset = User.objects.select_related("organization").all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        if self.action == "retrieve":
            return UserDetailSerializer
        if self.action == "create":
            return UserCreateSerializer
        return UserUpdateSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            return qs

        params = self.request.query_params
        search = params.get("search")
        role = params.get("role")
        organization_id = params.get("organization_id")
        is_active = parse_bool(params.get("is_active"))

        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(username__icontains=search) | Q(phone__icontains=search)
            )
        if role:
            qs = qs.filter(role=role)
        if organization_id and str(organization_id).isdigit():
            qs = qs.filter(organization_id=int(organization_id))
        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success_response(
            message="创建成功",
            data={"id": user.id, "username": user.username, "name": user.name, "role": user.role},
            http_status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=UserDetailSerializer(instance).data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="更新成功", data=UserDetailSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="更新成功", data=UserDetailSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            return error_response("不能删除自己", http_status=400)

        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return success_response(message="删除成功", http_status=status.HTTP_200_OK)

