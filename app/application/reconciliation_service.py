"""应用服务层：编排一次完整的对账流程。"""

import re
from pathlib import Path

import pandas as pd

from app.domain.reconcile import reconcile_orders
from app.infrastructure.excel_reader import read_excel_sheet
from app.models.reconciliation import InternalOrder, ReconciliationResult
from app.platforms.registry import get_platform_adapter, get_platform_spec


# 聚天下内部订单表的固定表名。
# 放在常量区便于后续维护（字段改名时集中修改）。
ORDER_LIST_SHEET = "订单列表"
PRODUCT_COLUMN = "产品内容"
ACTUAL_PEOPLE_COLUMN = "实到人数"
PURCHASE_AMOUNT_COLUMN = "采购金额"
INTEGER_TEXT_WITH_DECIMAL_SUFFIX = re.compile(r"^\d+\.0+$")


def run_reconciliation(
    jutianxia_file: Path,
    platform_file: Path,
    reconciliation_month: str,
    platform_name: str,
) -> ReconciliationResult:
    """执行对账主流程。

    流程顺序：
    1) 读取聚天下内部订单；
    2) 根据平台名选择对应适配器；
    3) 读取外部平台文件并解析成统一结构；
    4) 调用领域层算法做匹配与汇总；
    5) 合并结果并返回给上层（Web 路由）。
    """
    spec = get_platform_spec(platform_name)
    # Step 1: 读取内部订单（聚天下）。
    internal_orders = _load_internal_orders(
        jutianxia_file,
        order_column=spec.internal_order_column,
    )
    # Step 2: 根据平台名获取适配器（隔离平台差异）。
    adapter = get_platform_adapter(platform_name)
    # Step 3: 读取平台工作簿中的所有目标工作表，并交给适配器做清洗、过滤、聚合。
    workbook_data = _load_platform_workbook_data(
        platform_file=platform_file,
        worksheet_names=spec.worksheet_names,
        platform_name=platform_name,
    )
    platform_result = adapter.parse_workbook(
        workbook_data=workbook_data,
        reconciliation_month=reconciliation_month,
    )
    # Step 4: 调用领域算法做订单匹配与产品汇总。
    core_result = reconcile_orders(
        internal_orders=internal_orders,
        external_orders=platform_result.orders,
    )
    # Step 5: 合并领域结果与平台过滤统计，返回给 Web 层。
    return ReconciliationResult(
        rows=core_result.rows,
        matched_order_count=core_result.matched_order_count,
        unmatched_order_count=core_result.unmatched_order_count,
        filtered_out_of_month_row_count=platform_result.filtered_out_of_month_row_count,
        internal_only_order_nos=core_result.internal_only_order_nos,
        external_only_order_nos=core_result.external_only_order_nos,
    )


def _load_internal_orders(file_path: Path, order_column: str) -> list[InternalOrder]:
    """把聚天下 Excel 转成领域模型 InternalOrder 列表。

    约束：
    - 必须存在 `订单列表` 工作表；
    - 订单号为空的行会被丢弃（无法参与匹配）；
    - 数值字段转为 float，确保后续汇总类型一致。
    """
    dataframe = read_excel_sheet(
        file_path,
        ORDER_LIST_SHEET,
        dtype={order_column: str},
    )

    # 订单号为空的记录无法参与匹配，先过滤掉。
    working = dataframe[dataframe[order_column].notna()].copy()

    # 读取阶段负责保真，这里只做轻量清洗，并兼容旧数据里常见的 12345.0 文本格式。
    working[order_column] = working[order_column].astype(str).map(_normalize_order_no)

    orders = []
    for _, row in working.iterrows():
        orders.append(
            InternalOrder(
                order_no=str(row[order_column]),
                product_name=str(row[PRODUCT_COLUMN]),
                actual_people=float(row[ACTUAL_PEOPLE_COLUMN]),
                purchase_amount=float(row[PURCHASE_AMOUNT_COLUMN]),
            )
    )
    return orders


def _normalize_order_no(raw_value: str) -> str:
    """保留大订单号文本，同时兼容旧数据中的整数 + .0 文本。"""
    normalized = raw_value.strip()
    if INTEGER_TEXT_WITH_DECIMAL_SUFFIX.fullmatch(normalized):
        return normalized.split(".", 1)[0]
    return normalized


def _load_platform_workbook_data(
    platform_file: Path,
    worksheet_names: tuple[str, ...],
    platform_name: str,
) -> dict[str, pd.DataFrame]:
    """读取平台工作簿中约定的所有工作表。

    缺少指定工作表时，统一翻译成包含平台名和工作表名的业务错误，
    这样上层不需要理解 pandas 的底层异常文案。
    """
    workbook_data = {}
    for worksheet_name in worksheet_names:
        try:
            workbook_data[worksheet_name] = read_excel_sheet(platform_file, worksheet_name)
        except ValueError as exc:
            raise ValueError(f"平台 {platform_name} 缺少工作表: {worksheet_name}") from exc
    return workbook_data
