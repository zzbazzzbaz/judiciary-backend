"""绩效管理 API（管理员/网格负责人）。"""

from __future__ import annotations

from django.db.models import Avg, Count, Max, Min
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.pagination import StandardPageNumberPagination
from utils.permissions import IsGridManager
from utils.responses import error_response, success_response

from ..models import PerformanceScore, User
from ..serializers import PerformanceScoreSerializer, PerformanceScoreUpsertSerializer


class PerformanceScoreListCreateAPIView(APIView):
    """
    绩效打分与列表：
    - POST /api/v1/performance/scores/   网格负责人（含管理员）
    - GET  /api/v1/performance/scores/   管理员/网格负责人
    """

    permission_classes = [IsGridManager]

    def post(self, request, *args, **kwargs):
        serializer = PerformanceScoreUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mediator_id = serializer.validated_data["mediator_id"]
        score = serializer.validated_data["score"]
        period = serializer.validated_data["period"]
        comment = serializer.validated_data.get("comment")

        mediator = User.objects.filter(id=mediator_id, role=User.Role.MEDIATOR).first()
        if not mediator:
            return error_response("调解员不存在", code=404, http_status=404)

        # 同一调解员同一周期仅一条记录：存在则更新，不存在则创建
        obj, _created = PerformanceScore.objects.update_or_create(
            mediator=mediator,
            period=period,
            defaults={"score": score, "comment": comment, "scorer": request.user},
        )

        return success_response(message="打分成功", data=PerformanceScoreSerializer(obj).data)

    def get(self, request, *args, **kwargs):
        qs = PerformanceScore.objects.select_related("mediator", "scorer").all().order_by("-created_at")

        mediator_id = request.query_params.get("mediator_id")
        period = request.query_params.get("period")

        if mediator_id and str(mediator_id).isdigit():
            qs = qs.filter(mediator_id=int(mediator_id))
        if period:
            qs = qs.filter(period=period)

        paginator = StandardPageNumberPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = PerformanceScoreSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PerformanceStatisticsAPIView(APIView):
    """绩效统计（基础实现）。"""

    permission_classes = [IsGridManager]

    def get(self, request, *args, **kwargs):
        qs = PerformanceScore.objects.select_related("mediator").all()
        period = request.query_params.get("period")
        if period:
            qs = qs.filter(period=period)

        overall = qs.aggregate(
            total=Count("id"),
            avg_score=Avg("score"),
            max_score=Max("score"),
            min_score=Min("score"),
        )

        by_user = (
            qs.values("mediator_id", "mediator__name")
            .annotate(
                total=Count("id"),
                avg_score=Avg("score"),
                max_score=Max("score"),
                min_score=Min("score"),
            )
            .order_by("-avg_score")
        )

        return success_response(
            data={
                "overall": overall,
                "by_user": [
                    {
                        "mediator_id": row["mediator_id"],
                        "mediator_name": row["mediator__name"],
                        "total": row["total"],
                        "avg_score": row["avg_score"],
                        "max_score": row["max_score"],
                        "min_score": row["min_score"],
                    }
                    for row in by_user
                ],
            }
        )


class PerformanceUserDetailAPIView(APIView):
    """用户绩效详情。"""

    permission_classes = [IsGridManager]

    def get(self, request, user_id: int, *args, **kwargs):
        user = get_object_or_404(User, id=user_id)

        qs = (
            PerformanceScore.objects.filter(mediator=user)
            .select_related("scorer")
            .order_by("-period", "-created_at")
        )

        stats = qs.aggregate(avg_score=Avg("score"), max_score=Max("score"), min_score=Min("score"))
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

