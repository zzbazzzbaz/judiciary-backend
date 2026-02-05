"""
Cases 模块导入导出资源类

支持：
- 案件归档批量导入（Excel）
"""

from __future__ import annotations

from datetime import datetime

from import_export import resources, fields

from .models import CaseArchive


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
