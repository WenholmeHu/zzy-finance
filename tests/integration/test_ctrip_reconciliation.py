from pathlib import Path

import pandas as pd
import pytest

from app.application.reconciliation_service import _normalize_order_no, run_reconciliation

CTRIP_BLOCKED_DISTRIBUTORS = {
    "携程http://vbooking.ctrip.com/，VBK账号:vbk95089 密码:2117548aaa@ "
    "携程登录账号:13388601591密码:2117548aaa(子订单)",
    "杭州游趣旅游携程",
}


def test_ctrip_reconciliation_excludes_blocked_distributors_from_real_sample() -> None:
    base = Path(__file__).resolve().parents[2] / "test_data"
    jutianxia_file = base / "聚天下_携程.xlsx"
    ctrip_file = base / "携程.xlsx"
    if not jutianxia_file.exists() or not ctrip_file.exists():
        pytest.skip("当前 test_data 未包含携程真实样例文件")

    dataframe = pd.read_excel(jutianxia_file, sheet_name="订单列表")
    retail_amount = pd.to_numeric(dataframe["零售金额"], errors="coerce")
    distributor = dataframe["分销商"].fillna("").astype(str).str.strip()
    eligible = dataframe[dataframe["订单号"].notna() & ~retail_amount.eq(0)].copy()
    excluded_order_nos = {
        _normalize_order_no(str(order_no))
        for order_no in eligible.loc[
            distributor.isin(CTRIP_BLOCKED_DISTRIBUTORS),
            "订单号",
        ].tolist()
    }

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=ctrip_file,
        reconciliation_month="2026-03",
        platform_name="ctrip",
    )

    assert excluded_order_nos
    assert result.matched_order_count + result.unmatched_order_count == (
        len(eligible) - len(excluded_order_nos)
    )
    assert excluded_order_nos.isdisjoint(set(result.internal_only_order_nos))
