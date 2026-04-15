import pandas as pd
import pytest

from app.platforms.meituan_adapter import MeituanAdapter
from app.platforms.registry import get_platform_adapter


def test_meituan_adapter_filters_by_month_and_aggregates_orders() -> None:
    adapter = MeituanAdapter()
    dataframe = pd.DataFrame(
        [
            {
                "商家订单号": "14869628.0",
                "销售时间": "2026-03-29 21:47:42",
                "应付金额": 189.0,
                "技术服务费": 21.0,
                "技术服务费退款": 0.0,
                "商家承担优惠": 0.0,
                "结算金额": 189.0,
            },
            {
                "商家订单号": "14869628.0",
                "销售时间": "2026-03-29 22:00:00",
                "应付金额": 11.0,
                "技术服务费": 1.0,
                "技术服务费退款": -0.2,
                "商家承担优惠": 2.0,
                "结算金额": 8.8,
            },
            {
                "商家订单号": "14870192",
                "销售时间": "2026-04-01 08:29:51",
                "应付金额": 30.8,
                "技术服务费": 4.2,
                "技术服务费退款": 0.0,
                "商家承担优惠": 0.0,
                "结算金额": 30.8,
            },
        ]
    )

    result = adapter.parse_workbook(
        {"订单详情": dataframe},
        reconciliation_month="2026-03",
    )

    assert result.filtered_out_of_month_row_count == 1
    assert len(result.orders) == 1

    order = result.orders[0]
    assert order.external_order_no == "14869628"
    assert order.metrics["sales_amount"] == pytest.approx(200.0)
    assert order.metrics["technical_service_fee"] == pytest.approx(21.8)
    assert order.metrics["merchant_coupon"] == pytest.approx(2.0)
    assert order.metrics["settlement_paid"] == pytest.approx(197.8)
    assert order.platform_name == "meituan"
    assert order.source_row_count == 2


def test_meituan_adapter_requires_columns() -> None:
    adapter = MeituanAdapter()
    dataframe = pd.DataFrame([{"商家订单号": "14869628"}])

    with pytest.raises(ValueError, match="美团文件缺少必要字段"):
        adapter.parse_workbook(
            {"订单详情": dataframe},
            reconciliation_month="2026-03",
        )


def test_platform_registry_returns_meituan_adapter() -> None:
    adapter = get_platform_adapter("meituan")

    assert isinstance(adapter, MeituanAdapter)
