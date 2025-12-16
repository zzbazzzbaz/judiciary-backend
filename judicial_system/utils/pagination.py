"""自定义分页器（返回结构与需求文档一致）。"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPageNumberPagination(PageNumberPagination):
    """
    分页返回格式：
    {
      "code": 200,
      "message": "success",
      "data": { "total": 0, "page": 1, "page_size": 20, "list": [...] }
    }
    """

    page_query_param = "page"
    page_size_query_param = "page_size"
    page_size = 20
    max_page_size = 200

    def get_paginated_response(self, data):
        page_size = self.get_page_size(self.request) or self.page_size
        return Response(
            {
                "code": 200,
                "message": "success",
                "data": {
                    "total": self.page.paginator.count,
                    "page": self.page.number,
                    "page_size": page_size,
                    "list": data,
                },
            }
        )

