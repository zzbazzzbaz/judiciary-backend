"""机构管理 API（管理员/登录用户）。"""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from utils.responses import error_response, success_response
from utils.validators import parse_bool
from utils.permissions import IsAdmin

from ..models import Organization, User
from ..serializers import OrganizationCreateUpdateSerializer, OrganizationListSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    机构管理：
    - GET    /api/v1/organizations/             管理员（扁平列表）
    - POST   /api/v1/organizations/             管理员
    - GET    /api/v1/organizations/{id}/        管理员
    - PUT    /api/v1/organizations/{id}/        管理员
    - DELETE /api/v1/organizations/{id}/        管理员
    - GET    /api/v1/organizations/tree/        登录用户（树形结构）
    """

    queryset = Organization.objects.select_related("parent").all().order_by("sort_order", "id")
    pagination_class = None  # 需求文档未要求分页，直接返回列表

    def get_permissions(self):
        if self.action == "tree":
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return OrganizationCreateUpdateSerializer
        return OrganizationListSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        search = request.query_params.get("search")
        is_active = parse_bool(request.query_params.get("is_active"))

        if search:
            qs = qs.filter(name__icontains=search)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        data = OrganizationListSerializer(qs, many=True).data
        return success_response(data=data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = OrganizationCreateUpdateSerializer(instance).data
        # 详情补充 parent_id，便于前端回显
        data["parent_id"] = instance.parent_id
        return success_response(data=data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = serializer.save()
        return success_response(message="创建成功", data={"id": org.id, "name": org.name})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="更新成功", data=OrganizationCreateUpdateSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="更新成功", data=OrganizationCreateUpdateSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if Organization.objects.filter(parent=instance).exists():
            return error_response("该机构下存在子机构，无法删除", http_status=400)

        if User.objects.filter(organization=instance).exists():
            return error_response("该机构下存在用户，无法删除", http_status=400)

        instance.delete()
        return success_response(message="删除成功", http_status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request, *args, **kwargs):
        """机构树形结构（仅返回启用机构）。"""

        orgs = Organization.objects.filter(is_active=True).order_by("sort_order", "id")
        # 预先构建 parent_id -> children 映射，避免递归中频繁查询
        children_map: dict[int | None, list[Organization]] = {}
        for org in orgs:
            children_map.setdefault(org.parent_id, []).append(org)

        def build_node(node: Organization):
            return {
                "id": node.id,
                "name": node.name,
                "children": [build_node(child) for child in children_map.get(node.id, [])],
            }

        tree = [build_node(root) for root in children_map.get(None, [])]
        return success_response(data=tree)

