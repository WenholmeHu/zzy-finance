from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.application.reconciliation_service import run_reconciliation


def _find_workbook_by_sheet(sheet_name: str) -> Path:
    base = Path(__file__).resolve().parents[2] / "test_data"
    for path in base.glob("*.xlsx"):
        workbook = load_workbook(path, read_only=True, data_only=True)
        if sheet_name in workbook.sheetnames:
            return path
    raise FileNotFoundError(f"Could not find workbook containing sheet: {sheet_name}")


def test_sample_reconciliation_matches_expected_totals() -> None:
    jutianxia_file = _find_workbook_by_sheet("订单列表")
    ctrip_file = _find_workbook_by_sheet("流水")

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=ctrip_file,
        reconciliation_month="2026-03",
        platform_name="ctrip",
    )

    assert result.matched_order_count == 1908
    assert result.unmatched_order_count == 172
    assert result.filtered_out_of_month_row_count == 3
    assert result.product_count == 29
    assert result.internal_only_count == 172
    assert result.external_only_count == 0
    assert "14347370" in result.internal_only_order_nos
    assert result.external_only_order_nos == []

    rows_by_product = {row.product_name: row for row in result.rows}

    luzhai = rows_by_product["【即买即用】【线下扫码】东运旅行卢宅景区成人票+卢宅文创产品1份"]
    assert luzhai.actual_people_total == 746
    assert luzhai.sales_amount_total == pytest.approx(48490.0)
    assert luzhai.purchase_amount_total == pytest.approx(38792.0)
    assert luzhai.profit_total == pytest.approx(9698.0)

    liangzhu = rows_by_product["良渚古城遗址公园成人票（不含观光车）即买即用"]
    assert liangzhu.actual_people_total == 647
    assert liangzhu.sales_amount_total == pytest.approx(34996.5)
    assert liangzhu.purchase_amount_total == pytest.approx(25998.0)
    assert liangzhu.profit_total == pytest.approx(8998.5)

    huangdiling = rows_by_product["【提前两小时】黄帝陵景区  成人票"]
    assert huangdiling.actual_people_total == 349
    assert huangdiling.sales_amount_total == pytest.approx(23208.5)
    assert huangdiling.purchase_amount_total == pytest.approx(21987.0)
    assert huangdiling.profit_total == pytest.approx(1221.5)
