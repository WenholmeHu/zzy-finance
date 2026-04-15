import pandas as pd
import pytest

from app.platforms.douyin_adapter import DouyinAdapter
from app.platforms.registry import get_platform_adapter


def _make_row(
    order_no: str,
    writeoff_time: str,
    sales_amount: float,
    incremental_treasure: float,
    software_fee: float,
    platform_commission: float,
    creator_commission: float,
    brokerage_service_fee: float,
    insurance_fee: float,
    service_provider_commission: float,
    merchant_due: float,
) -> dict[str, object]:
    return {
        "核销时间": writeoff_time,
        "订单编号": order_no,
        "订单实收金额": sales_amount,
        "增量宝": incremental_treasure,
        "软件服务费": software_fee,
        "平台撮合佣金": platform_commission,
        "达人佣金": creator_commission,
        "撮合经纪服务费": brokerage_service_fee,
        "保险费用": insurance_fee,
        "服务商佣金": service_provider_commission,
        "商家应得": merchant_due,
    }


def test_douyin_adapter_requires_both_worksheets() -> None:
    adapter = DouyinAdapter()
    positive = pd.DataFrame(
        [
            _make_row(
                "1092863204608662040",
                "2026-03-05 10:00:00",
                100.0,
                1.0,
                2.0,
                3.0,
                4.0,
                0.0,
                0.0,
                0.0,
                30.0,
            )
        ]
    )

    with pytest.raises(ValueError, match="抖音文件缺少工作表: 分账明细-退款-团购"):
        adapter.parse_workbook(
            {"分账明细-正向-团购": positive},
            reconciliation_month="2026-03",
        )


@pytest.mark.parametrize("worksheet_name", ["分账明细-正向-团购", "分账明细-退款-团购"])
def test_douyin_adapter_validates_required_columns_per_worksheet(worksheet_name: str) -> None:
    adapter = DouyinAdapter()
    valid_dataframe = pd.DataFrame(
        [
            _make_row(
                "1092863204608662040",
                "2026-03-01 09:00:00",
                10.0,
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                7.0,
                8.0,
            )
        ]
    )
    invalid_dataframe = pd.DataFrame(
        [
            {
                "核销时间": "2026-03-01 09:00:00",
                "订单编号": "1092863204608662040",
                "订单实收金额": 10.0,
                "增量宝": 1.0,
                "软件服务费": 2.0,
            }
        ]
    )

    with pytest.raises(ValueError, match="抖音文件.*缺少必要字段"):
        adapter.parse_workbook(
            {
                "分账明细-正向-团购": invalid_dataframe if worksheet_name == "分账明细-正向-团购" else valid_dataframe,
                "分账明细-退款-团购": invalid_dataframe if worksheet_name == "分账明细-退款-团购" else valid_dataframe,
            },
            reconciliation_month="2026-03",
        )


def test_douyin_adapter_filters_by_month_and_aggregates_across_sheets() -> None:
    adapter = DouyinAdapter()
    positive = pd.DataFrame(
        [
            _make_row(
                "1092863204608662040",
                "2026-03-05 10:00:00",
                100.0,
                1.0,
                2.0,
                3.0,
                4.0,
                0.0,
                0.0,
                0.0,
                30.0,
            ),
            _make_row(
                "1092863204608662040",
                "2026-03-05 11:00:00",
                20.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                20.0,
            ),
            _make_row(
                "OUT-OF-MONTH",
                "2026-04-01 00:00:00",
                999.0,
                9.0,
                9.0,
                9.0,
                9.0,
                9.0,
                9.0,
                9.0,
                9.0,
            ),
        ]
    )
    refund = pd.DataFrame(
        [
            _make_row(
                "1092863204608662040",
                "2026-03-06 09:00:00",
                -188.35,
                0.42,
                0.0,
                3.44,
                1.0,
                0.0,
                0.0,
                0.0,
                -102.49,
            ),
            _make_row(
                "1092863204608662040",
                "2026-03-06 10:00:00",
                -0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ),
            _make_row(
                "REFUND-OUT-OF-MONTH",
                "2026-02-28 23:59:59",
                -1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ),
        ]
    )

    result = adapter.parse_workbook(
        {
            "分账明细-正向-团购": positive,
            "分账明细-退款-团购": refund,
        },
        reconciliation_month="2026-03",
    )

    assert result.filtered_out_of_month_row_count == 2
    assert len(result.orders) == 1

    order = result.orders[0]
    assert order.external_order_no == "1092863204608662040"
    assert order.source_row_count == 4
    assert order.metrics["sales_amount"] == -68.35
    assert order.metrics["technical_service_fee"] == 3.42
    assert order.metrics["commission"] == 12.44
    assert order.metrics["service_provider_commission"] == 0.0
    assert order.metrics["settlement_paid"] == -52.49


def test_douyin_adapter_registers_in_registry() -> None:
    adapter = get_platform_adapter("douyin")

    assert isinstance(adapter, DouyinAdapter)
