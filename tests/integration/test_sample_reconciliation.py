from pathlib import Path

import pandas as pd
import pytest
from openpyxl import Workbook

from app.application.reconciliation_service import _load_internal_orders, run_reconciliation
from app.models.reconciliation import PlatformParseResult
from app.platforms.base import PlatformSpec
from app.platforms.registry import get_platform_spec

CTRIP_BLOCKED_DISTRIBUTORS = {
    "携程http://vbooking.ctrip.com/，VBK账号:vbk95089 密码:2117548aaa@ "
    "携程登录账号:13388601591密码:2117548aaa(子订单)",
    "杭州游趣旅游携程",
}


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


def test_run_reconciliation_excludes_zero_retail_internal_orders_from_differences(
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
                "零售金额": 100.0,
            },
            {
                "订单号": "ZERO-001",
                "产品内容": "产品零",
                "实到人数": 1,
                "采购金额": 20.0,
                "零售金额": 0.0,
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
            }
        ],
    )

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=ctrip_file,
        reconciliation_month="2026-03",
        platform_name="ctrip",
    )

    assert result.matched_order_count == 1
    assert result.unmatched_order_count == 0
    assert result.internal_only_order_nos == []
    assert result.external_only_order_nos == []
    assert [row.product_name for row in result.rows] == ["产品A"]


def test_run_reconciliation_excludes_blocked_ctrip_distributors_from_internal_orders(
    tmp_path: Path,
) -> None:
    blocked_child_order_distributor, blocked_hangzhou_distributor = sorted(
        CTRIP_BLOCKED_DISTRIBUTORS
    )
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "A-001",
                "产品内容": "产品A",
                "实到人数": 2,
                "采购金额": 80.0,
                "零售金额": 100.0,
                "分销商": "普通分销商",
            },
            {
                "订单号": "DROP-001",
                "产品内容": "产品B",
                "实到人数": 1,
                "采购金额": 20.0,
                "零售金额": 20.0,
                "分销商": blocked_child_order_distributor,
            },
            {
                "订单号": "DROP-002",
                "产品内容": "产品C",
                "实到人数": 1,
                "采购金额": 30.0,
                "零售金额": 30.0,
                "分销商": blocked_hangzhou_distributor,
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
            }
        ],
    )

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=ctrip_file,
        reconciliation_month="2026-03",
        platform_name="ctrip",
    )

    assert result.matched_order_count == 1
    assert result.unmatched_order_count == 0
    assert result.internal_only_order_nos == []
    assert result.external_only_order_nos == []
    assert [row.product_name for row in result.rows] == ["产品A"]


def test_platform_specs_expose_worksheet_lists_and_match_columns() -> None:
    ctrip_spec = get_platform_spec("ctrip")
    assert ctrip_spec.worksheet_names == ("流水",)
    assert ctrip_spec.internal_order_column == "订单号"
    assert ctrip_spec.internal_difference_label == "订单号"
    assert ctrip_spec.external_difference_label == "第三方单号"

    meituan_spec = get_platform_spec("meituan")
    assert meituan_spec.worksheet_names == ("订单详情",)
    assert meituan_spec.internal_order_column == "订单号"
    assert meituan_spec.internal_difference_label == "订单号"
    assert meituan_spec.external_difference_label == "商家订单号"

    douyin_spec = get_platform_spec("douyin")
    assert douyin_spec.worksheet_names == ("分账明细-正向-团购", "分账明细-退款-团购")
    assert douyin_spec.internal_order_column == "渠道订单号"
    assert douyin_spec.internal_difference_label == "渠道订单号"
    assert douyin_spec.external_difference_label == "订单编号"


def test_run_reconciliation_loads_all_specified_worksheets_into_workbook_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
            }
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
            }
        ],
    )
    with pd.ExcelWriter(ctrip_file, mode="a", engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {
                    "退款单号": "R-001",
                    "退款金额": 12.0,
                }
            ]
        ).to_excel(writer, sheet_name="退款", index=False)

    fake_spec = PlatformSpec(
        platform_name="ctrip",
        platform_label="携程",
        worksheet_names=("流水", "退款"),
        internal_order_column="订单号",
        internal_difference_label="订单号",
        external_difference_label="第三方单号",
        adapter_factory=None,
    )

    class RecordingAdapter:
        def __init__(self) -> None:
            self.seen_workbook_data: dict[str, pd.DataFrame] | None = None

        def parse_workbook(
            self,
            workbook_data: dict[str, pd.DataFrame],
            reconciliation_month: str,
        ) -> PlatformParseResult:
            self.seen_workbook_data = workbook_data
            assert reconciliation_month == "2026-03"
            assert set(workbook_data) == {"流水", "退款"}
            assert workbook_data["流水"].iloc[0]["第三方单号"] == "A-001"
            assert workbook_data["退款"].iloc[0]["退款单号"] == "R-001"
            return PlatformParseResult(orders=[], filtered_out_of_month_row_count=0)

    adapter = RecordingAdapter()
    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_spec",
        lambda platform_name: fake_spec,
    )
    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_adapter",
        lambda platform_name: adapter,
    )

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=ctrip_file,
        reconciliation_month="2026-03",
        platform_name="ctrip",
    )

    assert adapter.seen_workbook_data is not None
    assert result.matched_order_count == 0
    assert result.filtered_out_of_month_row_count == 0


def test_run_reconciliation_raises_clear_error_when_a_specified_worksheet_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
            }
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
            }
        ],
    )
    fake_spec = PlatformSpec(
        platform_name="ctrip",
        platform_label="携程",
        worksheet_names=("流水", "退款"),
        internal_order_column="订单号",
        internal_difference_label="订单号",
        external_difference_label="第三方单号",
        adapter_factory=None,
    )

    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_spec",
        lambda platform_name: fake_spec,
    )
    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_adapter",
        lambda platform_name: object(),
    )

    with pytest.raises(ValueError, match="平台 ctrip 缺少工作表: 退款"):
        run_reconciliation(
            jutianxia_file=jutianxia_file,
            platform_file=ctrip_file,
            reconciliation_month="2026-03",
            platform_name="ctrip",
        )


def test_run_reconciliation_loads_the_only_dynamic_platform_worksheet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "TC-001",
                "产品内容": "产品A",
                "实到人数": 1,
                "采购金额": 18.0,
            }
        ],
    )
    tongcheng_file = _write_excel(
        tmp_path / "tongcheng.xlsx",
        "订单2026-04-01",
        [
            {
                "旅游日期": "2026-03-02",
                "应结(元)": 20.0,
                "三方流水号": "TC-001",
            }
        ],
    )

    fake_spec = PlatformSpec(
        platform_name="tongcheng",
        platform_label="同程",
        worksheet_names=(),
        worksheet_mode="single_dynamic",
        internal_order_column="订单号",
        internal_difference_label="订单号",
        external_difference_label="三方流水号",
        adapter_factory=None,
    )

    class RecordingAdapter:
        def __init__(self) -> None:
            self.seen_workbook_data: dict[str, pd.DataFrame] | None = None

        def parse_workbook(
            self,
            workbook_data: dict[str, pd.DataFrame],
            reconciliation_month: str,
        ) -> PlatformParseResult:
            self.seen_workbook_data = workbook_data
            assert reconciliation_month == "2026-03"
            assert list(workbook_data) == ["订单2026-04-01"]
            assert workbook_data["订单2026-04-01"].iloc[0]["三方流水号"] == "TC-001"
            return PlatformParseResult(orders=[], filtered_out_of_month_row_count=0)

    adapter = RecordingAdapter()
    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_spec",
        lambda platform_name: fake_spec,
    )
    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_adapter",
        lambda platform_name: adapter,
    )

    result = run_reconciliation(
        jutianxia_file=jutianxia_file,
        platform_file=tongcheng_file,
        reconciliation_month="2026-03",
        platform_name="tongcheng",
    )

    assert adapter.seen_workbook_data is not None
    assert result.matched_order_count == 0
    assert result.filtered_out_of_month_row_count == 0


def test_run_reconciliation_raises_clear_error_when_dynamic_platform_has_multiple_sheets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "TC-001",
                "产品内容": "产品A",
                "实到人数": 1,
                "采购金额": 18.0,
            }
        ],
    )
    tongcheng_file = _write_excel(
        tmp_path / "tongcheng.xlsx",
        "订单2026-04-01",
        [
            {
                "旅游日期": "2026-03-02",
                "应结(元)": 20.0,
                "三方流水号": "TC-001",
            }
        ],
    )
    with pd.ExcelWriter(tongcheng_file, mode="a", engine="openpyxl") as writer:
        pd.DataFrame([{"说明": "额外工作表"}]).to_excel(writer, sheet_name="说明", index=False)

    fake_spec = PlatformSpec(
        platform_name="tongcheng",
        platform_label="同程",
        worksheet_names=(),
        worksheet_mode="single_dynamic",
        internal_order_column="订单号",
        internal_difference_label="订单号",
        external_difference_label="三方流水号",
        adapter_factory=None,
    )

    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_spec",
        lambda platform_name: fake_spec,
    )
    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_adapter",
        lambda platform_name: object(),
    )

    with pytest.raises(ValueError, match="平台 tongcheng 必须且只能包含 1 个工作表"):
        run_reconciliation(
            jutianxia_file=jutianxia_file,
            platform_file=tongcheng_file,
            reconciliation_month="2026-03",
            platform_name="tongcheng",
        )


def test_run_reconciliation_raises_clear_error_when_platform_worksheet_mode_is_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "TC-001",
                "产品内容": "产品A",
                "实到人数": 1,
                "采购金额": 18.0,
            }
        ],
    )
    tongcheng_file = _write_excel(
        tmp_path / "tongcheng.xlsx",
        "订单2026-04-01",
        [
            {
                "旅游日期": "2026-03-02",
                "应结(元)": 20.0,
                "三方流水号": "TC-001",
            }
        ],
    )

    fake_spec = PlatformSpec(
        platform_name="tongcheng",
        platform_label="同程",
        worksheet_names=(),
        worksheet_mode="typo_mode",
        internal_order_column="订单号",
        internal_difference_label="订单号",
        external_difference_label="三方流水号",
        adapter_factory=None,
    )

    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_spec",
        lambda platform_name: fake_spec,
    )
    monkeypatch.setattr(
        "app.application.reconciliation_service.get_platform_adapter",
        lambda platform_name: object(),
    )

    with pytest.raises(ValueError, match="平台 tongcheng 的工作表加载模式不受支持: typo_mode"):
        run_reconciliation(
            jutianxia_file=jutianxia_file,
            platform_file=tongcheng_file,
            reconciliation_month="2026-03",
            platform_name="tongcheng",
        )


def test_load_internal_orders_uses_the_specified_match_column(tmp_path: Path) -> None:
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "IGNORED-001",
                "渠道订单号": "DY-001",
                "产品内容": "产品A",
                "实到人数": 2,
                "采购金额": 80.0,
            },
            {
                "订单号": "IGNORED-002",
                "渠道订单号": "DY-002",
                "产品内容": "产品B",
                "实到人数": 1,
                "采购金额": 40.0,
            },
        ],
    )

    orders = _load_internal_orders(jutianxia_file, order_column="渠道订单号")

    assert [order.order_no for order in orders] == ["DY-001", "DY-002"]


def test_load_internal_orders_excludes_zero_retail_amount_rows(tmp_path: Path) -> None:
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "KEEP-001",
                "产品内容": "产品A",
                "实到人数": 2,
                "采购金额": 80.0,
                "零售金额": 100.0,
            },
            {
                "订单号": "DROP-001",
                "产品内容": "产品B",
                "实到人数": 1,
                "采购金额": 40.0,
                "零售金额": 0.0,
            },
            {
                "订单号": "DROP-002",
                "产品内容": "产品C",
                "实到人数": 1,
                "采购金额": 20.0,
                "零售金额": "0.00",
            },
        ],
    )

    orders = _load_internal_orders(jutianxia_file, order_column="订单号")

    assert [order.order_no for order in orders] == ["KEEP-001"]


def test_load_internal_orders_excludes_blocked_ctrip_distributors_only_for_ctrip(
    tmp_path: Path,
) -> None:
    blocked_child_order_distributor, blocked_hangzhou_distributor = sorted(
        CTRIP_BLOCKED_DISTRIBUTORS
    )
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "KEEP-001",
                "产品内容": "产品A",
                "实到人数": 2,
                "采购金额": 80.0,
                "零售金额": 100.0,
                "分销商": "普通分销商",
            },
            {
                "订单号": "DROP-001",
                "产品内容": "产品B",
                "实到人数": 1,
                "采购金额": 40.0,
                "零售金额": 40.0,
                "分销商": blocked_child_order_distributor,
            },
            {
                "订单号": "DROP-002",
                "产品内容": "产品C",
                "实到人数": 1,
                "采购金额": 20.0,
                "零售金额": 20.0,
                "分销商": blocked_hangzhou_distributor,
            },
        ],
    )

    ctrip_orders = _load_internal_orders(
        jutianxia_file,
        order_column="订单号",
        platform_name="ctrip",
    )
    meituan_orders = _load_internal_orders(
        jutianxia_file,
        order_column="订单号",
        platform_name="meituan",
    )

    assert [order.order_no for order in ctrip_orders] == ["KEEP-001"]
    assert [order.order_no for order in meituan_orders] == [
        "KEEP-001",
        "DROP-001",
        "DROP-002",
    ]


def test_load_internal_orders_preserves_large_order_numbers_as_strings(
    tmp_path: Path,
) -> None:
    jutianxia_file = tmp_path / "jutianxia.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "订单列表"
    sheet.append(["订单号", "渠道订单号", "产品内容", "实到人数", "采购金额"])
    sheet.append([14877492, "1093177561710100507", "产品A", 1, 44.11])
    sheet.append([14877472, "12345.0", "产品B", 1, 88.22])
    workbook.save(jutianxia_file)

    raw_values = pd.read_excel(jutianxia_file, sheet_name="订单列表")["渠道订单号"].tolist()

    orders = _load_internal_orders(jutianxia_file, order_column="渠道订单号")

    assert isinstance(raw_values[0], float)
    assert str(raw_values[0]) != "1093177561710100507"
    assert raw_values[1] == 12345.0
    assert [order.order_no for order in orders] == [
        "1093177561710100507",
        "12345",
    ]


def test_load_internal_orders_reads_numeric_cells_as_plain_order_numbers(
    tmp_path: Path,
) -> None:
    jutianxia_file = tmp_path / "jutianxia_numeric.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "订单列表"
    sheet.append(["订单号", "渠道订单号", "产品内容", "实到人数", "采购金额"])
    sheet.append([14877492, 12345.0, "产品A", 1, 44.11])
    workbook.save(jutianxia_file)

    orders = _load_internal_orders(jutianxia_file, order_column="渠道订单号")

    assert [order.order_no for order in orders] == ["12345"]
