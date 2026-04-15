from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app


def _write_excel(path: Path, sheet_name: str, rows: list[dict]) -> Path:
    dataframe = pd.DataFrame(rows)
    with pd.ExcelWriter(path) as writer:
        dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    return path


def _write_workbook(path: Path, sheets: dict[str, list[dict]]) -> Path:
    with pd.ExcelWriter(path) as writer:
        for sheet_name, rows in sheets.items():
            dataframe = pd.DataFrame(rows)
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    return path


def test_reconcile_route_renders_summary_and_table(tmp_path: Path) -> None:
    client = TestClient(app)
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia.xlsx",
        "订单列表",
        [
            {
                "订单号": "A-001",
                "产品内容": "测试产品A",
                "实到人数": 2,
                "采购金额": 80.0,
            },
            {
                "订单号": "B-001",
                "产品内容": "测试产品B",
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
                "第三方单号": "A-001",
                "结算价金额": 50.0,
                "出发时间": "2026-03-03",
            },
            {
                "第三方单号": "X-999",
                "结算价金额": 10.0,
                "出发时间": "2026-03-04",
            },
            {
                "第三方单号": "OUT-001",
                "结算价金额": 99.0,
                "出发时间": "2026-04-01",
            },
        ],
    )

    with jutianxia_file.open("rb") as jutianxia_stream, ctrip_file.open("rb") as ctrip_stream:
        response = client.post(
            "/reconcile",
            data={
                "reconciliation_month": "2026-03",
                "platform": "ctrip",
            },
            files={
                "jutianxia_file": (
                    jutianxia_file.name,
                    jutianxia_stream,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
                "platform_file": (
                    ctrip_file.name,
                    ctrip_stream,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
        )

    assert response.status_code == 200
    assert "成功匹配订单数" in response.text
    assert ">1<" in response.text
    assert "汇总产品数" in response.text
    assert response.text.count(">1<") >= 2
    assert "被过滤的非当月平台记录数" in response.text
    assert ">1<" in response.text
    assert "结果总览" in response.text
    assert "主结果表" in response.text
    assert "订单差异检查" in response.text
    assert "产品名称" in response.text
    assert "核销人次" in response.text
    assert "销售额" in response.text
    assert "结算实付" in response.text
    assert "采购金额" in response.text
    assert "利润" in response.text
    assert "聚天下有、第三方当月无" in response.text
    assert "第三方有、聚天下当月无" in response.text
    assert response.text.count(">序号<") == 2
    assert response.text.count(">订单号<") >= 1
    assert response.text.count(">第三方单号<") >= 1
    assert "B-001" in response.text
    assert "X-999" in response.text
    assert response.text.count("<details") == 2
    assert "测试产品A" in response.text
    assert "导出 Excel" in response.text
    assert "导出差异表" in response.text


def test_reconcile_route_renders_douyin_platform_and_headers(tmp_path: Path) -> None:
    client = TestClient(app)
    jutianxia_file = _write_excel(
        tmp_path / "jutianxia_douyin.xlsx",
        "订单列表",
        [
            {
                "渠道订单号": "DY-001",
                "产品内容": "抖音产品A",
                "实到人数": 2,
                "销售金额": 200.0,
                "技术服务费": 10.0,
                "佣金": 5.0,
                "服务商佣金": 3.0,
                "结算实付": 182.0,
                "采购金额": 150.0,
                "利润": 32.0,
            }
        ],
    )
    douyin_file = _write_workbook(
        tmp_path / "douyin.xlsx",
        {
            "分账明细-正向-团购": [
                {
                    "核销时间": "2026-03-02",
                    "订单编号": "DY-001",
                    "订单实收金额": 200.0,
                    "增量宝": 3.0,
                    "软件服务费": 7.0,
                    "平台撮合佣金": 2.0,
                    "达人佣金": 1.0,
                    "撮合经纪服务费": 1.0,
                    "保险费用": 1.0,
                    "服务商佣金": 3.0,
                    "商家应得": 182.0,
                }
            ],
            "分账明细-退款-团购": [
                {
                    "核销时间": "2026-03-02",
                    "订单编号": "DY-001",
                    "订单实收金额": 0.0,
                    "增量宝": 0.0,
                    "软件服务费": 0.0,
                    "平台撮合佣金": 0.0,
                    "达人佣金": 0.0,
                    "撮合经纪服务费": 0.0,
                    "保险费用": 0.0,
                    "服务商佣金": 0.0,
                    "商家应得": 0.0,
                }
            ],
        },
    )

    with jutianxia_file.open("rb") as jutianxia_stream, douyin_file.open("rb") as douyin_stream:
        response = client.post(
            "/reconcile",
            data={
                "reconciliation_month": "2026-03",
                "platform": "douyin",
            },
            files={
                "jutianxia_file": (
                    jutianxia_file.name,
                    jutianxia_stream,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
                "platform_file": (
                    douyin_file.name,
                    douyin_stream,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
        )

    assert response.status_code == 200
    assert 'value="douyin"' in response.text
    assert "产品名称" in response.text
    assert "核销人次" in response.text
    assert "销售额" in response.text
    assert "技术服务费" in response.text
    assert "佣金" in response.text
    assert "服务商佣金" in response.text
    assert "结算实付" in response.text
    assert "采购金额" in response.text
    assert "利润" in response.text
    assert "渠道订单号" in response.text
    assert "订单编号" in response.text
