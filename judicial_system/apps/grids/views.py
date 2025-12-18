"""网格视图"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Grid
from .serializers import GridWithPersonnelSerializer


class GridViewSet(viewsets.ReadOnlyModelViewSet):
    """
    网格列表接口（无需登录）

    - GET /api/v1/grids/ - 获取网格列表及每个网格下的人员（不分页）
    - GET /api/v1/grids/{id}/ - 获取单个网格详情及人员
    """

    queryset = (
        Grid.objects.filter(is_active=True)
        .select_related("current_manager")
        .prefetch_related("mediator_assignments__mediator")
        .order_by("id")
    )
    serializer_class = GridWithPersonnelSerializer
    permission_classes = [AllowAny]  # 无需登录
    pagination_class = None  # 禁用分页
