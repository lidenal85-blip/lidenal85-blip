from fastapi.testclient import TestClient
from survey_finder.bootstrap.app import create_app

client = TestClient(create_app())

def test_leader_endpoint():
    r = client.get("/leader")
    assert "is_leader" in r.json()
