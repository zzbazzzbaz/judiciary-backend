"""
通用校验工具

说明：
- 该模块用于 users 子应用的输入校验（用户名、密码、身份证、手机号等）。
"""

from __future__ import annotations

import re
from datetime import datetime


_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{4,20}$")
_PHONE_RE = re.compile(r"^\d{11}$")
_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


def validate_username(username: str) -> bool:
    """用户名格式校验：字母数字下划线，4-20 位。"""

    return bool(username and _USERNAME_RE.fullmatch(username))


def validate_password_strength(password: str) -> bool:
    """
    密码强度校验：
    - 至少 6 位
    - 同时包含字母和数字
    """

    if not password or len(password) < 6:
        return False
    has_alpha = any(ch.isalpha() for ch in password)
    has_digit = any(ch.isdigit() for ch in password)
    return has_alpha and has_digit


def validate_phone(phone: str) -> bool:
    """手机号格式校验：11 位数字。"""

    return bool(phone and _PHONE_RE.fullmatch(phone))


def validate_period(period: str) -> bool:
    """考核周期格式校验：YYYY-MM。"""

    if not period or not _PERIOD_RE.fullmatch(period):
        return False
    # 进一步校验月份范围
    try:
        datetime.strptime(period, "%Y-%m")
    except ValueError:
        return False
    return True


def validate_id_card(id_card: str) -> bool:
    """
    身份证号校验（18 位二代身份证）。

    校验规则：
    - 前 17 位为数字
    - 最后一位为数字或 X
    - 校验码符合 GB 11643-1999 规则
    """

    if not id_card or len(id_card) != 18:
        return False

    body, check = id_card[:17], id_card[17].upper()
    if not body.isdigit() or (not check.isdigit() and check != "X"):
        return False

    # 出生日期简单校验（YYYYMMDD）
    birth = id_card[6:14]
    try:
        datetime.strptime(birth, "%Y%m%d")
    except ValueError:
        return False

    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    mapping = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]
    total = sum(int(num) * w for num, w in zip(body, weights))
    return mapping[total % 11] == check


def parse_bool(value: str | None):
    """解析 querystring 中的布尔值（true/false/1/0）。"""

    if value is None:
        return None
    v = str(value).strip().lower()
    if v in {"1", "true", "yes", "y"}:
        return True
    if v in {"0", "false", "no", "n"}:
        return False
    return None

