"""领域层：纯业务对账算法，不依赖 Web/Excel 等外部技术细节。"""

from collections import defaultdict

from app.models.reconciliation import (
    ExternalOrderAggregate,
    InternalOrder,
    ProductSummaryRow,
    ReconciliationResult,
)


def reconcile_orders(
    internal_orders: list[InternalOrder],
    external_orders: list[ExternalOrderAggregate],
) -> ReconciliationResult:
    """按“内部订单号 = 外部订单号”匹配，并按产品维度汇总。

    返回值包含：
    - 每个产品的汇总行；
    - 匹配成功/失败的订单计数。
    """
    # 将外部订单建成字典，后续查找从 O(n) 降到 O(1)。
    external_index = {order.external_order_no: order for order in external_orders}

    # 分组桶：key 是产品名称，value 是当前产品的累计指标。
    grouped: dict[str, defaultdict[str, float]] = defaultdict(lambda: defaultdict(float))
    matched_order_count = 0
    unmatched_order_count = 0
    internal_order_nos = {order.order_no for order in internal_orders}
    external_order_nos = {order.external_order_no for order in external_orders}

    for internal_order in internal_orders:
        # 以“内部订单号 == 外部订单号”作为唯一匹配规则。
        external_order = external_index.get(internal_order.order_no)
        if external_order is None:
            unmatched_order_count += 1
            continue

        matched_order_count += 1
        bucket = grouped[internal_order.product_name]
        bucket["actual_people"] += internal_order.actual_people
        bucket["purchase_amount"] += internal_order.purchase_amount
        for metric_name, metric_value in external_order.metrics.items():
            bucket[metric_name] += metric_value

    rows = []
    # 排序后输出，保证页面和导出结果稳定，便于复核。
    for product_name, totals in sorted(grouped.items()):
        totals["profit"] = totals["settlement_paid"] - totals["purchase_amount"]
        rows.append(
            ProductSummaryRow(
                product_name=product_name,
                metrics=dict(totals),
            )
        )

    # 差异清单用于页面“订单差异检查”模块，按字符串排序便于人工核对。
    internal_only_order_nos = sorted(internal_order_nos - external_order_nos)
    external_only_order_nos = sorted(external_order_nos - internal_order_nos)

    return ReconciliationResult(
        rows=rows,
        matched_order_count=matched_order_count,
        unmatched_order_count=unmatched_order_count,
        internal_only_order_nos=internal_only_order_nos,
        external_only_order_nos=external_only_order_nos,
    )
