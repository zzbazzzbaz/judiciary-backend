"""
Cases 模块导入导出资源类

支持：
- 案件归档批量导入（Excel）
- 任务批量导入（Excel）
"""

from __future__ import annotations

from datetime import datetime

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from apps.grids.models import Grid
from apps.users.models import User

from .models import CaseArchive, Task, TaskType, Town


class CaseArchiveResource(resources.ModelResource):
    """
    案件归档导入资源类。

    字段映射：
    - 序号 → serial_number
    - 申请人* → applicant
    - 被申请人* → respondent
    - 案由* → case_reason
    - 受理时间* → acceptance_time (YYYY-MM-DD)
    - 承办人员* → handler
    - 适用程序* → applicable_procedure
    - 结案时间* → closure_time (YYYY-MM-DD)
    - 结案方式* → closure_method
    - 案号* → case_number
    """

    serial_number = fields.Field(column_name="序号", attribute="serial_number")
    applicant = fields.Field(column_name="申请人*", attribute="applicant")
    respondent = fields.Field(column_name="被申请人*", attribute="respondent")
    case_reason = fields.Field(column_name="案由*", attribute="case_reason")
    acceptance_time = fields.Field(column_name="受理时间*", attribute="acceptance_time")
    handler = fields.Field(column_name="承办人员*", attribute="handler")
    applicable_procedure = fields.Field(column_name="适用程序*", attribute="applicable_procedure")
    closure_time = fields.Field(column_name="结案时间*", attribute="closure_time")
    closure_method = fields.Field(column_name="结案方式*", attribute="closure_method")
    case_number = fields.Field(column_name="案号*", attribute="case_number")

    class Meta:
        model = CaseArchive
        # 排除 id 字段，导入时自动生成
        exclude = ("id",)
        # 使用案号作为导入标识字段（用于判断是新增还是更新）
        import_id_fields = ["case_number"]
        fields = (
            "serial_number",
            "applicant",
            "respondent",
            "case_reason",
            "acceptance_time",
            "handler",
            "applicable_procedure",
            "closure_time",
            "closure_method",
            "case_number",
        )
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

    def before_import_row(self, row, row_number=None, **kwargs):
        """导入前的数据预处理和校验。"""
        # 必填字段校验
        applicant = row.get("申请人*", "").strip() if row.get("申请人*") else ""
        respondent = row.get("被申请人*", "").strip() if row.get("被申请人*") else ""
        case_reason = row.get("案由*", "").strip() if row.get("案由*") else ""
        handler = row.get("承办人员*", "").strip() if row.get("承办人员*") else ""
        applicable_procedure = row.get("适用程序*", "").strip() if row.get("适用程序*") else ""
        closure_method = row.get("结案方式*", "").strip() if row.get("结案方式*") else ""
        case_number = row.get("案号*", "").strip() if row.get("案号*") else ""

        if not applicant:
            raise ValueError("申请人不能为空")
        if not respondent:
            raise ValueError("被申请人不能为空")
        if not case_reason:
            raise ValueError("案由不能为空")
        if not handler:
            raise ValueError("承办人员不能为空")
        if not applicable_procedure:
            raise ValueError("适用程序不能为空")
        if not closure_method:
            raise ValueError("结案方式不能为空")
        if not case_number:
            raise ValueError("案号不能为空")

        # 受理时间格式处理
        acceptance_time = row.get("受理时间*")
        if not acceptance_time:
            raise ValueError("受理时间不能为空")
        if isinstance(acceptance_time, datetime):
            row["受理时间*"] = acceptance_time.date()
        elif isinstance(acceptance_time, str):
            acceptance_time = acceptance_time.strip()
            try:
                row["受理时间*"] = datetime.strptime(acceptance_time, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"受理时间「{acceptance_time}」格式错误，应为 YYYY-MM-DD")

        # 结案时间格式处理
        closure_time = row.get("结案时间*")
        if not closure_time:
            raise ValueError("结案时间不能为空")
        if isinstance(closure_time, datetime):
            row["结案时间*"] = closure_time.date()
        elif isinstance(closure_time, str):
            closure_time = closure_time.strip()
            try:
                row["结案时间*"] = datetime.strptime(closure_time, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"结案时间「{closure_time}」格式错误，应为 YYYY-MM-DD")

        # 序号处理（可为空）
        serial_number = row.get("序号", "")
        if serial_number:
            row["序号"] = str(serial_number).strip()


class ActiveNameWidget(ForeignKeyWidget):
    """按名称查找启用状态的记录，未找到返回 None。"""

    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        val = str(value).strip()
        if not val:
            return None
        return self.model.objects.filter(**{self.field: val, "is_active": True}).first()


class MediatorPhoneWidget(ForeignKeyWidget):
    """按手机号查找启用状态的调解员。"""

    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        phone = str(value).strip()
        if phone.endswith(".0"):
            phone = phone[:-2]
        if not phone:
            return None
        return User.objects.filter(
            phone=phone, role=User.Role.MEDIATOR, is_active=True
        ).first()


class TaskResource(resources.ModelResource):
    """
    任务导入资源类。

    字段映射：
    - 任务类型 → task_type（按名称查找 TaskType，可为空）
    - 所属镇 → town（按名称查找 Town）
    - 所属网格 → grid（按名称查找 Grid）
    - 上报人手机号* → reporter（按手机号查找调解员）
    - 任务描述* → description
    - 涉及金额 → amount
    - 当事人姓名* → party_name
    - 当事人电话 → party_phone
    - 当事人住址 → party_address
    - 上报地址 → report_address
    """

    task_type = fields.Field(
        column_name="任务类型",
        attribute="task_type",
        widget=ActiveNameWidget(TaskType, field="name"),
    )
    town = fields.Field(
        column_name="所属镇",
        attribute="town",
        widget=ActiveNameWidget(Town, field="name"),
    )
    grid = fields.Field(
        column_name="所属网格",
        attribute="grid",
        widget=ActiveNameWidget(Grid, field="name"),
    )
    reporter = fields.Field(
        column_name="上报人手机号*",
        attribute="reporter",
        widget=MediatorPhoneWidget(User, field="phone"),
    )
    description = fields.Field(column_name="任务描述*", attribute="description")
    amount = fields.Field(column_name="涉及金额", attribute="amount")
    party_name = fields.Field(column_name="当事人姓名*", attribute="party_name")
    party_phone = fields.Field(column_name="当事人电话", attribute="party_phone")
    party_address = fields.Field(column_name="当事人住址", attribute="party_address")
    report_address = fields.Field(column_name="上报地址", attribute="report_address")

    class Meta:
        model = Task
        fields = (
            "task_type",
            "town",
            "grid",
            "reporter",
            "description",
            "amount",
            "party_name",
            "party_phone",
            "party_address",
            "report_address",
        )
        skip_unchanged = True
        report_skipped = True
        use_transactions = True

    def get_instance(self, instance_loader, row):
        """始终创建新任务记录。"""
        return None

    @staticmethod
    def _is_empty_row(row):
        """检查是否为空行（所有关键字段均为空）。"""
        key_columns = ["任务描述*", "当事人姓名*", "上报人手机号*"]
        return all(not str(row.get(col) or "").strip() for col in key_columns)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """跳过空行。"""
        if self._is_empty_row(row):
            return True
        return super().skip_row(instance, original, row, import_validation_errors)

    def before_import_row(self, row, row_number=None, **kwargs):
        """导入前的数据预处理和校验。"""
        # 跳过空行
        if self._is_empty_row(row):
            return

        # ---- 必填字段校验 ----
        task_type_name = str(row.get("任务类型") or "").strip()
        if task_type_name and not TaskType.objects.filter(name=task_type_name, is_active=True).exists():
            raise ValueError(f"任务类型「{task_type_name}」不存在或未启用")

        description = str(row.get("任务描述*") or "").strip()
        if not description:
            raise ValueError("任务描述不能为空")

        party_name = str(row.get("当事人姓名*") or "").strip()
        if not party_name:
            raise ValueError("当事人姓名不能为空")

        reporter_phone_val = str(row.get("上报人手机号*") or "").strip()
        if reporter_phone_val.endswith(".0"):
            reporter_phone_val = reporter_phone_val[:-2]
        if not reporter_phone_val:
            raise ValueError("上报人手机号不能为空")
        row["上报人手机号*"] = reporter_phone_val  # 回写清理后的值给 Widget

        if not User.objects.filter(
            phone=reporter_phone_val, role=User.Role.MEDIATOR, is_active=True
        ).exists():
            raise ValueError(f"手机号「{reporter_phone_val}」对应的调解员不存在或未启用")

        # ---- 可选 FK 校验 ----
        town_name = str(row.get("所属镇") or "").strip()
        if town_name and not Town.objects.filter(name=town_name, is_active=True).exists():
            raise ValueError(f"所属镇「{town_name}」不存在或未启用")

        grid_name = str(row.get("所属网格") or "").strip()
        if grid_name and not Grid.objects.filter(name=grid_name, is_active=True).exists():
            raise ValueError(f"所属网格「{grid_name}」不存在或未启用")

        # ---- 涉及金额处理 ----
        amount = row.get("涉及金额")
        if amount is not None and str(amount).strip() != "":
            try:
                row["涉及金额"] = float(str(amount).strip())
            except (ValueError, TypeError):
                raise ValueError(f"涉及金额「{amount}」格式错误，应为数字")
        else:
            row["涉及金额"] = None

        # ---- 当事人电话处理（Excel 可能读为浮点数）----
        party_phone_val = str(row.get("当事人电话") or "").strip()
        if party_phone_val.endswith(".0"):
            party_phone_val = party_phone_val[:-2]
        row["当事人电话"] = party_phone_val if party_phone_val else ""

    def before_save_instance(self, instance, row, **kwargs):
        """保存前自动生成编号和设置状态。"""
        from utils.code_generator import generate_task_code

        instance.status = Task.Status.REPORTED
        instance.code = generate_task_code(
            task_type_id=instance.task_type_id if instance.task_type else None
        )
