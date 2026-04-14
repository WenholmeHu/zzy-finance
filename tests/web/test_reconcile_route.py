from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app


def _write_excel(path: Path, sheet_name: str, rows: list[dict]) -> Path:
    dataframe = pd.DataFrame(rows)
    with pd.ExcelWriter(path) as writer:
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
