from pathlib import Path

import pytest

from app.application.reconciliation_service import run_reconciliation


def test_tongcheng_reconciliation_matches_expected_totals_from_real_sample() -> None:
    base = Path(__file__).resolve().parents[2] / "test_data"
    jutianxia_file = base / "jutianxia_tc.xlsx"
    tongcheng_file = base / "tongcheng.xlsx"

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=tongcheng_file,
        reconciliation_month="2026-03",
        platform_name="tongcheng",
    )

    assert result.matched_order_count == 737
    assert result.unmatched_order_count == 8743
    assert result.product_count == 23
    assert result.filtered_out_of_month_row_count == 0
    assert result.internal_only_count == 8743
    assert result.external_only_count == 0
    assert result.external_only_order_nos == []

    row = next(
        row
        for row in result.rows
        if row.product_name == "【即买即用】【线下扫码】东运旅行卢宅景区成人票+卢宅文创产品1份"
    )
    assert row.metrics["actual_people"] == 257
    assert row.metrics["sales_amount"] == pytest.approx(16705.0)
    assert row.metrics["settlement_paid"] == pytest.approx(16705.0)
    assert row.metrics["purchase_amount"] == pytest.approx(13364.0)
    assert row.metrics["profit"] == pytest.approx(3341.0)
