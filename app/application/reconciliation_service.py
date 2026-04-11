"""应用服务层：编排一次完整的对账流程。"""

from pathlib import Path

from app.domain.reconcile import reconcile_orders
from app.infrastructure.excel_reader import read_excel_sheet
from app.models.reconciliation import InternalOrder, ReconciliationResult
from app.platforms.registry import get_platform_adapter


# 聚天下内部订单表的固定表名与字段名。
# 放在常量区便于后续维护（字段改名时集中修改）。
ORDER_LIST_SHEET = "订单列表"
ORDER_NO_COLUMN = "订单号"
PRODUCT_COLUMN = "产品内容"
ACTUAL_PEOPLE_COLUMN = "实到人数"
PURCHASE_AMOUNT_COLUMN = "采购金额"


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
    internal_orders = _load_internal_orders(jutianxia_file)
    adapter = get_platform_adapter(platform_name)
    platform_dataframe = read_excel_sheet(platform_file, adapter.worksheet_name)
    platform_result = adapter.parse(
        dataframe=platform_dataframe,
        reconciliation_month=reconciliation_month,
    )
    core_result = reconcile_orders(
        internal_orders=internal_orders,
        external_orders=platform_result.orders,
    )
    return ReconciliationResult(
        rows=core_result.rows,
        matched_order_count=core_result.matched_order_count,
        unmatched_order_count=core_result.unmatched_order_count,
        filtered_out_of_month_row_count=platform_result.filtered_out_of_month_row_count,
        internal_only_order_nos=core_result.internal_only_order_nos,
        external_only_order_nos=core_result.external_only_order_nos,
    )


def _load_internal_orders(file_path: Path) -> list[InternalOrder]:
    """把聚天下 Excel 转成领域模型 InternalOrder 列表。"""
    dataframe = read_excel_sheet(file_path, ORDER_LIST_SHEET)

    # 订单号为空的记录无法参与匹配，先过滤掉。
    working = dataframe[dataframe[ORDER_NO_COLUMN].notna()].copy()

    # Excel 里订单号常被读成浮点（例如 12345.0），这里统一清洗为纯字符串编号。
    working[ORDER_NO_COLUMN] = (
        working[ORDER_NO_COLUMN].astype(str).str.replace(".0", "", regex=False)
    )

    orders = []
    for _, row in working.iterrows():
        orders.append(
            InternalOrder(
                order_no=str(row[ORDER_NO_COLUMN]),
                product_name=str(row[PRODUCT_COLUMN]),
                actual_people=float(row[ACTUAL_PEOPLE_COLUMN]),
                purchase_amount=float(row[PURCHASE_AMOUNT_COLUMN]),
            )
        )
    return orders
