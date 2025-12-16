"""
地理坐标工具函数

用于 grids 子应用的边界坐标校验与中心点计算。
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


def validate_boundary(boundary: list) -> bool:
    """
    验证边界坐标格式：
    - 必须是数组
    - 至少 3 个点
    - 每个点是 [lng, lat] 格式
    - 坐标需在中国境内（粗略范围）
    """

    if not isinstance(boundary, list) or len(boundary) < 3:
        return False

    for point in boundary:
        if not isinstance(point, list) or len(point) != 2:
            return False
        lng, lat = point
        if not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
            return False
        # 中国境内坐标范围（与需求文档保持一致）
        if not (73.66 <= float(lng) <= 135.05 and 3.86 <= float(lat) <= 53.55):
            return False

    return True


def calculate_center(boundary: Iterable[list]) -> tuple[Decimal | None, Decimal | None]:
    """
    计算边界的中心点（取所有点的平均值）。

    返回：
    - (center_lng, center_lat)，保留 7 位小数
    """

    points = list(boundary) if boundary else []
    if not points:
        return None, None

    lng_sum = sum(float(point[0]) for point in points)
    lat_sum = sum(float(point[1]) for point in points)
    count = len(points)

    center_lng = Decimal(str(lng_sum / count)).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
    center_lat = Decimal(str(lat_sum / count)).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
    return center_lng, center_lat

