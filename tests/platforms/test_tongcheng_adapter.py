import pandas as pd
import pytest

from app.platforms.registry import get_platform_adapter
from app.platforms.tongcheng_adapter import TongchengAdapter


def test_tongcheng_adapter_filters_by_month_and_aggregates_orders() -> None:
    adapter = TongchengAdapter()
    dataframe = pd.DataFrame(
        [
            {
                "旅游日期": "2026-03-29",
                "应结(元)": 189.0,
                "三方流水号": "14869628.0",
            },
            {
                "旅游日期": "2026-03-29",
                "应结(元)": 11.0,
                "三方流水号": "14869628.0",
            },
            {
                "旅游日期": "2026-04-01",
                "应结(元)": 30.8,
                "三方流水号": "14870192",
            },
        ]
    )

    result = adapter.parse_workbook(
        {"订单2026-04-01": dataframe},
        reconciliation_month="2026-03",
    )

    assert result.filtered_out_of_month_row_count == 1
    assert len(result.orders) == 1

    order = result.orders[0]
    assert order.external_order_no == "14869628"
    assert order.metrics["sales_amount"] == pytest.approx(200.0)
    assert order.metrics["settlement_paid"] == pytest.approx(200.0)
    assert order.platform_name == "tongcheng"
    assert order.source_row_count == 2


def test_tongcheng_adapter_requires_columns() -> None:
    adapter = TongchengAdapter()
    dataframe = pd.DataFrame([{"三方流水号": "14869628"}])

    with pytest.raises(ValueError, match="同程文件缺少必要字段"):
        adapter.parse_workbook(
            {"订单2026-04-01": dataframe},
            reconciliation_month="2026-03",
        )


def test_platform_registry_returns_tongcheng_adapter() -> None:
    adapter = get_platform_adapter("tongcheng")

    assert isinstance(adapter, TongchengAdapter)
