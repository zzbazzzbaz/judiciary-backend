"""网格序列化器"""

from rest_framework import serializers

from apps.users.models import User

from .models import Grid, MediatorAssignment


class UserSimpleSerializer(serializers.ModelSerializer):
    """用户简单信息序列化器"""

    class Meta:
        model = User
        fields = ["id", "username", "name", "phone", "role"]


class GridWithPersonnelSerializer(serializers.ModelSerializer):
    """网格及人员信息序列化器"""

    # 网格负责人信息
    current_manager = UserSimpleSerializer(read_only=True)

    # 网格下的调解员列表
    mediators = serializers.SerializerMethodField()

    class Meta:
        model = Grid
        fields = [
            "id",
            "name",
            "region",
            "boundary",
            "center_lng",
            "center_lat",
            "current_manager",
            "mediators",
            "description",
            "is_active",
        ]

    def get_mediators(self, obj):
        """获取网格下的调解员列表"""
        # 通过 MediatorAssignment 获取分配到该网格的调解员
        assignments = obj.mediator_assignments.select_related("mediator").all()
        mediators = [assignment.mediator for assignment in assignments]
        return UserSimpleSerializer(mediators, many=True).data
