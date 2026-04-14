from pathlib import Path

import pandas as pd
import pytest

from app.application.reconciliation_service import run_reconciliation


def _write_excel(path: Path, sheet_name: str, rows: list[dict]) -> Path:
    dataframe = pd.DataFrame(rows)
    with pd.ExcelWriter(path) as writer:
        dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    return path


def test_ctrip_reconciliation_matches_expected_totals_from_workbooks(
    tmp_path: Path,
) -> None:
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "A-001",
                "产品内容": "产品A",
                "实到人数": 2,
                "采购金额": 80.0,
            },
            {
                "订单号": "A-002",
                "产品内容": "产品A",
                "实到人数": 1,
                "采购金额": 40.0,
            },
            {
                "订单号": "B-001",
                "产品内容": "产品B",
                "实到人数": 1,
                "采购金额": 20.0,
            },
        ],
    )
    ctrip_file = _write_excel(
        tmp_path / "ctrip.xlsx",
        "流水",
        [
            {
                "第三方单号": "A-001",
                "结算价金额": 100.0,
                "出发时间": "2026-03-02",
            },
            {
                "第三方单号": "A-002",
                "结算价金额": 50.0,
                "出发时间": "2026-03-03",
            },
            {
                "第三方单号": "X-999",
                "结算价金额": 99.0,
                "出发时间": "2026-03-03",
            },
            {
                "第三方单号": "OUT-001",
                "结算价金额": 88.0,
                "出发时间": "2026-04-01",
            },
        ],
    )

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=ctrip_file,
        reconciliation_month="2026-03",
        platform_name="ctrip",
    )

    assert result.matched_order_count == 2
    assert result.unmatched_order_count == 1
    assert result.filtered_out_of_month_row_count == 1
    assert result.product_count == 1
    assert result.internal_only_order_nos == ["B-001"]
    assert result.external_only_order_nos == ["X-999"]

    row = result.rows[0]
    assert row.product_name == "产品A"
    assert row.metrics["actual_people"] == 3
    assert row.metrics["sales_amount"] == pytest.approx(150.0)
    assert row.metrics["settlement_paid"] == pytest.approx(150.0)
    assert row.metrics["purchase_amount"] == pytest.approx(120.0)
    assert row.metrics["profit"] == pytest.approx(30.0)
