"""
Users 模块导入导出资源类

支持：
- 调解员批量导入（Excel）
- 培训记录批量导入（Excel）
"""

from __future__ import annotations

import re
from datetime import datetime

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from apps.grids.models import Grid
from .models import Organization, TrainingRecord, User


class OrganizationWidget(ForeignKeyWidget):
    """机构外键Widget，根据名称匹配机构。"""

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        value = str(value).strip()
        try:
            return self.model.objects.get(name=value)
        except self.model.DoesNotExist:
            raise ValueError(f"机构「{value}」不存在")
        except self.model.MultipleObjectsReturned:
            raise ValueError(f"机构「{value}」存在多个匹配项，请确保名称唯一")


class GridWidget(ForeignKeyWidget):
    """网格外键Widget，根据名称匹配网格。"""

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        value = str(value).strip()
        try:
            return self.model.objects.get(name=value, is_active=True)
        except self.model.DoesNotExist:
            raise ValueError(f"网格「{value}」不存在或未启用")
        except self.model.MultipleObjectsReturned:
            raise ValueError(f"网格「{value}」存在多个匹配项，请确保名称唯一")


class UserWidget(ForeignKeyWidget):
    """用户外键Widget，根据姓名匹配用户。"""

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            raise ValueError("姓名不能为空")
        value = str(value).strip()
        try:
            return self.model.objects.get(name=value)
        except self.model.DoesNotExist:
            raise ValueError(f"人员「{value}」不存在")
        except self.model.MultipleObjectsReturned:
            raise ValueError(f"人员「{value}」存在多个匹配项，请确保姓名唯一或使用用户名导入")


class MediatorResource(resources.ModelResource):
    """
    调解员导入资源类。

    字段映射：
    - 用户名* → username
    - 姓名* → name
    - 性别 → gender (男/女 → male/female)
    - 身份证号 → id_card
    - 联系电话 → phone
    - 所属机构 → organization (名称匹配)
    - 所属网格 → grid (名称匹配)
    - 是否启用 → is_active (是/否 → True/False)
    """

    username = fields.Field(column_name="用户名*", attribute="username")
    name = fields.Field(column_name="姓名*", attribute="name")
    gender = fields.Field(column_name="性别", attribute="gender")
    id_card = fields.Field(column_name="身份证号", attribute="id_card")
    phone = fields.Field(column_name="联系电话", attribute="phone")
    organization = fields.Field(
        column_name="所属机构",
        attribute="organization",
        widget=OrganizationWidget(Organization, field="name"),
    )
    grid = fields.Field(
        column_name="所属网格",
        attribute="grid",
        widget=GridWidget(Grid, field="name"),
    )
    is_active = fields.Field(column_name="是否启用", attribute="is_active")

    class Meta:
        model = User
        import_id_fields = ["username"]
        fields = ("username", "name", "gender", "id_card", "phone", "organization", "grid", "is_active")
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

    def before_import_row(self, row, row_number=None, **kwargs):
        """导入前的数据预处理和校验。"""
        # 必填字段校验
        username = row.get("用户名*", "").strip() if row.get("用户名*") else ""
        name = row.get("姓名*", "").strip() if row.get("姓名*") else ""

        if not username:
            raise ValueError("用户名不能为空")
        if not name:
            raise ValueError("姓名不能为空")

        # 用户名唯一性校验
        if User.objects.filter(username=username).exists():
            raise ValueError(f"用户名「{username}」已存在")

        # 性别转换
        gender_value = row.get("性别", "")
        if gender_value:
            gender_value = str(gender_value).strip()
            if gender_value == "男":
                row["性别"] = "male"
            elif gender_value == "女":
                row["性别"] = "female"
            elif gender_value not in ("male", "female", ""):
                raise ValueError(f"性别「{gender_value}」无效，请填写「男」或「女」")

        # 身份证号格式校验
        id_card = row.get("身份证号", "")
        if id_card:
            id_card = str(id_card).strip()
            if len(id_card) != 18:
                raise ValueError(f"身份证号「{id_card}」格式错误，应为18位")
            row["身份证号"] = id_card

        # 联系电话格式校验
        phone = row.get("联系电话", "")
        if phone:
            phone = str(phone).strip()
            # 移除可能的浮点数后缀（Excel有时会把数字当成浮点数）
            if phone.endswith(".0"):
                phone = phone[:-2]
            if not re.match(r"^1[3-9]\d{9}$", phone):
                raise ValueError(f"联系电话「{phone}」格式错误")
            row["联系电话"] = phone

        # 是否启用转换
        is_active = row.get("是否启用", "是")
        if is_active:
            is_active = str(is_active).strip()
            if is_active in ("是", "1", "True", "true", "TRUE"):
                row["是否启用"] = True
            elif is_active in ("否", "0", "False", "false", "FALSE"):
                row["是否启用"] = False
            else:
                row["是否启用"] = True  # 默认启用
        else:
            row["是否启用"] = True

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        """导入后设置默认值。"""
        # 设置角色为调解员
        instance.role = User.Role.MEDIATOR
        # 设置默认密码
        if new:
            instance.set_password("123456")


class TrainingRecordResource(resources.ModelResource):
    """
    培训记录导入资源类。

    字段映射：
    - 姓名* → user (通过姓名匹配用户)
    - 培训名称* → name
    - 培训内容 → content
    - 培训时间 → training_time (YYYY-MM-DD)
    """

    user = fields.Field(
        column_name="姓名*",
        attribute="user",
        widget=UserWidget(User, field="name"),
    )
    name = fields.Field(column_name="培训名称*", attribute="name")
    content = fields.Field(column_name="培训内容", attribute="content")
    training_time = fields.Field(column_name="培训时间", attribute="training_time")

    class Meta:
        model = TrainingRecord
        fields = ("user", "name", "content", "training_time")
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

    def get_instance(self, instance_loader, row):
        """检查重复记录（同一用户 + 同一培训名称 + 同一培训时间）。"""
        return None  # 始终创建新记录，由 before_import_row 处理重复检查

    def before_import_row(self, row, row_number=None, **kwargs):
        """导入前的数据预处理和校验。"""
        # 必填字段校验
        user_name = row.get("姓名*", "").strip() if row.get("姓名*") else ""
        training_name = row.get("培训名称*", "").strip() if row.get("培训名称*") else ""

        if not user_name:
            raise ValueError("姓名不能为空")
        if not training_name:
            raise ValueError("培训名称不能为空")

        # 培训时间格式处理
        training_time = row.get("培训时间")
        if training_time:
            if isinstance(training_time, datetime):
                row["培训时间"] = training_time.date()
            elif isinstance(training_time, str):
                training_time = training_time.strip()
                try:
                    row["培训时间"] = datetime.strptime(training_time, "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError(f"培训时间「{training_time}」格式错误，应为 YYYY-MM-DD")

        # 重复记录检查
        try:
            user = User.objects.get(name=user_name)
            training_time_value = row.get("培训时间")
            if TrainingRecord.objects.filter(
                user=user,
                name=training_name,
                training_time=training_time_value
            ).exists():
                raise ValueError(f"培训记录已存在（{user_name} - {training_name} - {training_time_value}）")
        except User.DoesNotExist:
            pass  # 用户不存在的错误会在 Widget 中抛出
