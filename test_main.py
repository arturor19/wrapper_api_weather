from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_read_contry():
    response = client.get("/weather?country=MX&city=Zapopan")
    assert response.status_code == 200

def test_error():
    response = client.get("/weather?country=MG&city=Zapopan")
    assert response.status_code == 404