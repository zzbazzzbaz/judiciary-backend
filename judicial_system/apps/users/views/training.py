"""培训记录 API（管理员）。"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.permissions import IsAdmin
from utils.responses import success_response

from ..models import TrainingRecord, User
from ..serializers import TrainingRecordCreateUpdateSerializer, TrainingRecordSerializer


class UserTrainingRecordAPIView(APIView):
    """
    用户培训记录列表/新增（管理员）。

    - GET  /api/v1/users/{id}/trainings/
    - POST /api/v1/users/{id}/trainings/
    """

    permission_classes = [IsAdmin]

    def get(self, request, user_id: int, *args, **kwargs):
        user = get_object_or_404(User, id=user_id)
        records = (
            TrainingRecord.objects.filter(user=user)
            .order_by("-training_time", "-created_at")
            .all()
        )
        return success_response(data=TrainingRecordSerializer(records, many=True).data)

    def post(self, request, user_id: int, *args, **kwargs):
        user = get_object_or_404(User, id=user_id)
        serializer = TrainingRecordCreateUpdateSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return success_response(message="创建成功", data=TrainingRecordSerializer(record).data)


class TrainingRecordDetailAPIView(APIView):
    """培训记录更新/删除（管理员）。"""

    permission_classes = [IsAdmin]

    def put(self, request, pk: int, *args, **kwargs):
        record = get_object_or_404(TrainingRecord, id=pk)
        serializer = TrainingRecordCreateUpdateSerializer(record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="更新成功", data=TrainingRecordSerializer(record).data)

    def delete(self, request, pk: int, *args, **kwargs):
        record = get_object_or_404(TrainingRecord, id=pk)
        record.delete()
        return success_response(message="删除成功")

