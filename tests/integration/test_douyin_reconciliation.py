from pathlib import Path

import pytest

from app.application.reconciliation_service import run_reconciliation


def test_douyin_reconciliation_matches_expected_totals_from_real_sample() -> None:
    base = Path(__file__).resolve().parents[2] / "test_data"
    jutianxia_file = base / "jutianxia.xlsx"
    douyin_file = base / "douyin.xlsx"
    if not jutianxia_file.exists() or not douyin_file.exists():
        pytest.skip("当前 test_data 未包含抖音真实样例文件")

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=douyin_file,
        reconciliation_month="2026-03",
        platform_name="douyin",
    )

    assert result.matched_order_count == 1838
    assert result.unmatched_order_count == 0
    assert result.product_count == 6
    assert result.filtered_out_of_month_row_count == 9
    assert result.internal_only_count == 0
    assert result.external_only_count == 1
    assert result.internal_only_order_nos == []
    assert result.external_only_order_nos == ["1091502369578909793"]

    row = next(
        row
        for row in result.rows
        if row.product_name == "益行远方文旅体惠民年卡(太湖源店)"
    )
    assert row.metrics["actual_people"] == 1
    assert row.metrics["sales_amount"] == pytest.approx(48.9)
    assert row.metrics["technical_service_fee"] == pytest.approx(-2.44)
    assert row.metrics["commission"] == pytest.approx(-4.09)
    assert row.metrics["service_provider_commission"] == pytest.approx(0.0)
    assert row.metrics["settlement_paid"] == pytest.approx(42.37)
    assert row.metrics["purchase_amount"] == pytest.approx(44.11)
    assert row.metrics["profit"] == pytest.approx(-1.74)


def test_douyin_reconciliation_produces_differences_from_internal_and_external_order_numbers() -> None:
    base = Path(__file__).resolve().parents[2] / "test_data"
    jutianxia_file = base / "jutianxia.xlsx"
    douyin_file = base / "douyin.xlsx"
    if not jutianxia_file.exists() or not douyin_file.exists():
        pytest.skip("当前 test_data 未包含抖音真实样例文件")

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=douyin_file,
        reconciliation_month="2026-03",
        platform_name="douyin",
    )

    assert result.internal_only_order_nos == []
    assert result.external_only_order_nos == ["1091502369578909793"]
    assert all(order_no.isdigit() for order_no in result.external_only_order_nos)
