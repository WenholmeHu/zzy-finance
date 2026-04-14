from fastapi.testclient import TestClient

from app.main import app


def test_home_page_renders_successfully() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "对账月份" in response.text
    assert "平台选择" in response.text
    assert "携程" in response.text
    assert "美团" in response.text
    assert "聚天下文件" in response.text
    assert "外部平台文件" in response.text
    assert "开始对账" in response.text
