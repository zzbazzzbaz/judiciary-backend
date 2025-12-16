"""机构管理 API（管理员/登录用户）。"""

from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from utils.permissions import IsAdmin
from utils.responses import success_response
from utils.validators import parse_bool

from ..models import Organization
from ..serializers import OrganizationListSerializer


class OrganizationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    机构管理：
    - GET /api/v1/organizations/        管理员（扁平列表）
    - GET /api/v1/organizations/tree/   登录用户（树形结构）
    """

    queryset = Organization.objects.select_related("parent").all().order_by("sort_order", "id")
    pagination_class = None  # 需求文档未要求分页，直接返回列表
    serializer_class = OrganizationListSerializer

    def get_permissions(self):
        if self.action == "tree":
            return [IsAuthenticated()]
        return [IsAdmin()]

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
