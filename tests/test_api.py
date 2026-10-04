from fastapi.testclient import TestClient

from app.main import app


def test_calculate_history_and_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_DATABASE_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        calculation = client.post("/api/calculate", json={"expression": "(2+3)*4"})
        assert calculation.status_code == 201
        body = calculation.json()
        assert body["result"] == 20

        history = client.get("/api/history").json()
        assert history["total"] == 1
        assert history["items"][0]["expression"] == "(2+3)*4"

        deleted = client.delete(f"/api/history/{body['history_id']}")
        assert deleted.status_code == 200
        assert client.get("/api/history").json()["total"] == 0


def test_bad_expression_is_not_saved(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_DATABASE_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        response = client.post("/api/calculate", json={"expression": "1/0"})
        assert response.status_code == 400
        assert response.json()["success"] is False
        assert client.get("/api/history").json()["total"] == 0
