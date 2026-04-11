import json
from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.main import app


def test_export_route_returns_excel_file() -> None:
    client = TestClient(app)
    payload = json.dumps(
        {
            "reconciliation_month": "2026-03",
            "platform_name": "ctrip",
            "rows": [
                {
                    "product_name": "测试产品",
                    "actual_people_total": 3,
                    "sales_amount_total": 150.0,
                    "settlement_paid_total": 150.0,
                    "purchase_amount_total": 120.0,
                    "profit_total": 30.0,
                }
            ],
        },
        ensure_ascii=False,
    )

    response = client.post("/export", data={"payload": payload})

    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment;" in response.headers["content-disposition"]

    workbook = load_workbook(BytesIO(response.content))
    worksheet = workbook["对账结果"]

    assert worksheet["A1"].value == "对账月份"
    assert worksheet["B1"].value == "2026-03"
    assert worksheet["A2"].value == "平台"
    assert worksheet["B2"].value == "携程"
    assert worksheet["A4"].value == "产品名称"
    assert worksheet["A5"].value == "测试产品"
    assert worksheet["B5"].value == 3
    assert worksheet["C5"].value == 150
    assert worksheet["F5"].value == 30
    assert workbook.sheetnames == ["对账结果"]
