"""
腾讯地图 API 封装

注意：
- 该模块会发起外部 HTTP 请求（requests）。
- 业务侧需要在 settings 中配置 `TENCENT_MAP_KEY`。
"""

from __future__ import annotations

from typing import Any

import requests
from django.conf import settings


def reverse_geocode(lat: float, lng: float) -> dict[str, Any] | None:
    """
    逆地址解析：坐标转地址。

    返回：
    - 成功：包含 address / province / city / district / street 的字典
    - 失败：None
    """

    url = "https://apis.map.qq.com/ws/geocoder/v1/"
    params = {
        "location": f"{lat},{lng}",
        "key": getattr(settings, "TENCENT_MAP_KEY", ""),
        "get_poi": 0,
    }

    response = requests.get(url, params=params, timeout=5)
    data = response.json()

    if data.get("status") == 0:
        result = data.get("result", {}) or {}
        address_component = result.get("address_component", {}) or {}
        return {
            "address": result.get("address", "") or "",
            "province": address_component.get("province", "") or "",
            "city": address_component.get("city", "") or "",
            "district": address_component.get("district", "") or "",
            "street": address_component.get("street", "") or "",
        }

    return None
