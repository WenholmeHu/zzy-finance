"""Web 路由层：处理页面请求、文件上传与导出下载。

职责边界：
- 负责 HTTP 请求和模板渲染；
- 不直接写对账算法；
- 通过 application 层串联业务流程。
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import asdict

from fastapi import APIRouter, File, Form, Request, Response, UploadFile
from fastapi.templating import Jinja2Templates

from app.application.reconciliation_service import run_reconciliation
from app.infrastructure.excel_writer import (
    build_difference_workbook,
    build_reconciliation_workbook,
)
from app.platforms.report_definitions import (
    get_platform_label,
    get_platform_report_definition,
    list_platform_report_definitions,
)


router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _base_context() -> dict:
    """模板渲染的默认上下文，保证初次加载和异常场景字段完整。"""
    # 统一提供全部模板字段，可避免模板中出现未定义变量异常。
    # 新增页面字段时，建议先在这里补默认值。
    return {
        "page_title": "本地对账工具",
        "selected_platform": "ctrip",
        "selected_month": "",
        "platform_options": [
            {
                "platform_name": definition.platform_name,
                "platform_label": definition.platform_label,
            }
            for definition in list_platform_report_definitions()
        ],
        "summary": None,
        "report_columns": [],
        "result_rows": [],
        "internal_only_order_nos": [],
        "external_only_order_nos": [],
        "error_message": None,
        "export_payload": "",
        "difference_export_payload": "",
    }


def _platform_label(platform_name: str) -> str:
    """平台内部代号转显示名称。"""
    try:
        return get_platform_label(platform_name)
    except ValueError:
        return platform_name


@router.get("/")
def index(request: Request):
    """首页：返回上传与结果展示页面。"""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_base_context(),
    )


@router.post("/reconcile")
async def reconcile(
    request: Request,
    reconciliation_month: str = Form(...),
    platform: str = Form(...),
    jutianxia_file: UploadFile = File(...),
    platform_file: UploadFile = File(...),
):
    """接收两个 Excel 文件并执行一次对账。"""
    context = _base_context()
    context["selected_platform"] = platform
    context["selected_month"] = reconciliation_month

    try:
        # 上传文件先落到临时目录，避免占用项目目录并便于自动清理。
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jutianxia_path = temp_path / jutianxia_file.filename
            platform_path = temp_path / platform_file.filename
            jutianxia_path.write_bytes(await jutianxia_file.read())
            platform_path.write_bytes(await platform_file.read())

            result = run_reconciliation(
                jutianxia_file=jutianxia_path,
                platform_file=platform_path,
                reconciliation_month=reconciliation_month,
                platform_name=platform,
            )

        # 构建页面摘要区与明细表数据。
        # 这里使用 dict 结构是为了让模板层直取字段，降低模板复杂度。
        context["summary"] = {
            "matched_order_count": result.matched_order_count,
            "product_count": result.product_count,
            "filtered_out_of_month_row_count": result.filtered_out_of_month_row_count,
            "internal_only_count": result.internal_only_count,
            "external_only_count": result.external_only_count,
            "platform_label": _platform_label(platform),
            "reconciliation_month": reconciliation_month,
        }
        report_definition = get_platform_report_definition(platform)
        context["report_columns"] = [asdict(column) for column in report_definition.columns]
        context["result_rows"] = [asdict(row) for row in result.rows]
        context["internal_only_order_nos"] = result.internal_only_order_nos
        context["external_only_order_nos"] = result.external_only_order_nos

        # 将导出所需数据序列化到隐藏字段，供 /export 接口再次使用。
        # 好处：用户不需要再次上传文件，就能导出“当前页面”对应的结果。
        context["export_payload"] = json.dumps(
            {
                "reconciliation_month": reconciliation_month,
                "platform_name": platform,
                "report_columns": context["report_columns"],
                "rows": context["result_rows"],
            },
            ensure_ascii=False,
        )
        context["difference_export_payload"] = json.dumps(
            {
                "reconciliation_month": reconciliation_month,
                "platform_name": platform,
                "internal_only_order_nos": context["internal_only_order_nos"],
                "external_only_order_nos": context["external_only_order_nos"],
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        # 统一转成页面提示，避免后端异常直接中断请求。
        # 若后续要区分用户错误/系统错误，可在此按异常类型细分文案。
        context["error_message"] = str(exc)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )


@router.post("/export")
async def export_excel(payload: str = Form(...)) -> Response:
    """根据前端提交的 payload 生成并下载 Excel。"""
    # payload 来源于隐藏字段，结构由 /reconcile 中构建并约定。
    parsed_payload = json.loads(payload)
    platform_name = parsed_payload["platform_name"]
    workbook_bytes = build_reconciliation_workbook(
        reconciliation_month=parsed_payload["reconciliation_month"],
        platform_label=_platform_label(platform_name),
        report_columns=parsed_payload.get("report_columns")
        or [asdict(column) for column in get_platform_report_definition(platform_name).columns],
        rows=parsed_payload["rows"],
    )
    filename = f"reconciliation_{platform_name}_{parsed_payload['reconciliation_month']}.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(
        content=workbook_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.post("/export-differences")
async def export_differences_excel(payload: str = Form(...)) -> Response:
    """根据前端提交的 payload 生成并下载差异订单 Excel。"""
    parsed_payload = json.loads(payload)
    platform_name = parsed_payload["platform_name"]
    workbook_bytes = build_difference_workbook(
        reconciliation_month=parsed_payload["reconciliation_month"],
        platform_label=_platform_label(platform_name),
        internal_only_order_nos=parsed_payload.get("internal_only_order_nos", []),
        external_only_order_nos=parsed_payload.get("external_only_order_nos", []),
    )
    filename = (
        f"difference_orders_{platform_name}_{parsed_payload['reconciliation_month']}.xlsx"
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(
        content=workbook_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
