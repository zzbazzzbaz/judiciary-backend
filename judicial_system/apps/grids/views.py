"""网格视图"""

from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Grid
from .serializers import GridCreateSerializer, GridWithPersonnelSerializer


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


class GridCreateView(APIView):
    """
    网格创建接口（无需认证）

    - POST /api/v1/grids/create/
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        创建网格
        请求参数：
        {
            "name": "网格名称",
            "boundary": [[lng, lat], [lng, lat], ...]
        }
        """
        serializer = GridCreateSerializer(data=request.data)
        if serializer.is_valid():
            grid = serializer.save()
            return Response(
                {
                    "code": 200,
                    "message": "创建成功",
                    "data": {
                        "id": grid.id,
                        "name": grid.name,
                        "boundary": grid.boundary,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"code": 400, "message": "参数错误", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
