"""绩效管理 API。"""

from __future__ import annotations

from django.db.models import Avg, Max, Min
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.responses import success_response

from ..models import PerformanceScore, User


class PerformanceUserDetailAPIView(APIView):
    """获取当前用户历史绩效。"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # 获取当前登录用户
        user = request.user

        # 查询该用户的所有历史绩效记录
        qs = (
            PerformanceScore.objects.filter(mediator=user)
            .select_related("scorer")
            .order_by("-period", "-created_at")
        )

        # 统计平均分、最高分、最低分
        stats = qs.aggregate(avg_score=Avg("score"), max_score=Max("score"), min_score=Min("score"))

        # 构建历史记录列表
        records = [
            {
                "period": obj.period,
                "score": obj.score,
                "comment": obj.comment or "",
                "scorer_name": obj.scorer.name if obj.scorer else None,
            }
            for obj in qs
        ]

        return success_response(
            data={
                "user_id": user.id,
                "user_name": user.name,
                **stats,
                "records": records,
            }
        )
