from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_templates_csv():
    resp = client.get("/templates/datapoints.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    lines = resp.text.strip().splitlines()
    assert lines[0].startswith("# erlaubte Codes:")
    assert lines[1] == "esrs_code,value,unit,source"
