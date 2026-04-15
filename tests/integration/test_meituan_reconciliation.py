from pathlib import Path

import pytest

from app.application.reconciliation_service import run_reconciliation
from app.platforms.report_definitions import get_platform_report_definition


def test_meituan_reconciliation_matches_expected_totals_from_real_sample() -> None:
    base = Path(__file__).resolve().parents[2] / "test_data"
    jutianxia_file = base / "jutianxia.xlsx"
    meituan_file = base / "meituan.xlsx"
    if not jutianxia_file.exists() or not meituan_file.exists():
        pytest.skip("当前 test_data 未包含美团真实样例文件")

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=meituan_file,
        reconciliation_month="2026-03",
        platform_name="meituan",
    )

    assert result.matched_order_count == 2852
    assert result.unmatched_order_count == 348
    assert result.filtered_out_of_month_row_count == 2515
    assert result.product_count == 26
    assert result.internal_only_count == 348
    assert result.external_only_count == 68
    assert result.internal_only_order_nos[:3] == ["14304449", "14304450", "14546871"]
    assert result.external_only_order_nos[:3] == ["14753956", "14757189", "14757193"]

    rows_by_product = {row.product_name: row for row in result.rows}

    luzhai = rows_by_product["【即买即用】东运旅行卢宅景区成人票+卢宅文创产品1份"]
    assert luzhai.metrics["actual_people"] == 172
    assert luzhai.metrics["sales_amount"] == pytest.approx(9838.4)
    assert luzhai.metrics["technical_service_fee"] == pytest.approx(1341.6)
    assert luzhai.metrics["merchant_coupon"] == pytest.approx(0.0)
    assert luzhai.metrics["settlement_paid"] == pytest.approx(9838.4)
    assert luzhai.metrics["purchase_amount"] == pytest.approx(8944.0)
    assert luzhai.metrics["profit"] == pytest.approx(894.4)

    lingshan = rows_by_product["【即买即用】OTA 杭州灵山幻境景交车"]
    assert lingshan.metrics["actual_people"] == 20
    assert lingshan.metrics["sales_amount"] == pytest.approx(600.0)
    assert lingshan.metrics["technical_service_fee"] == pytest.approx(0.0)
    assert lingshan.metrics["merchant_coupon"] == pytest.approx(-33.0)
    assert lingshan.metrics["settlement_paid"] == pytest.approx(567.0)
    assert lingshan.metrics["purchase_amount"] == pytest.approx(600.0)
    assert lingshan.metrics["profit"] == pytest.approx(-33.0)


def test_meituan_report_definition_exposes_eight_columns() -> None:
    definition = get_platform_report_definition("meituan")

    assert [column.label for column in definition.columns] == [
        "产品名称",
        "核销人次",
        "销售额",
        "技术服务费",
        "优惠券（商家承担）",
        "结算实付",
        "采购金额",
        "利润",
    ]
