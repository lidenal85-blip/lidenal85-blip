from fastapi.testclient import TestClient
from survey_finder.bootstrap.app import create_app
client = TestClient(create_app())
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
