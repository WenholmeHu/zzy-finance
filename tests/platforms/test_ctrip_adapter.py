import pandas as pd

from app.platforms.ctrip_adapter import CtripAdapter
from app.platforms.registry import get_platform_adapter


def test_ctrip_adapter_filters_by_month_and_aggregates_orders() -> None:
    adapter = CtripAdapter()
    dataframe = pd.DataFrame(
        [
            {
                "第三方单号": "A-001",
                "结算价金额": 100.0,
                "出发时间": "2026-03-02",
            },
            {
                "第三方单号": "A-001",
                "结算价金额": 50.0,
                "出发时间": "2026-03-02",
            },
            {
                "第三方单号": "B-001",
                "结算价金额": 40.0,
                "出发时间": "2026-04-01",
            },
        ]
    )

    result = adapter.parse(dataframe=dataframe, reconciliation_month="2026-03")

    assert result.filtered_out_of_month_row_count == 1
    assert len(result.orders) == 1

    order = result.orders[0]
    assert order.external_order_no == "A-001"
    assert order.settlement_amount == 150.0
    assert order.platform_name == "ctrip"
    assert order.source_row_count == 2


def test_platform_registry_returns_ctrip_adapter() -> None:
    adapter = get_platform_adapter("ctrip")

    assert isinstance(adapter, CtripAdapter)
