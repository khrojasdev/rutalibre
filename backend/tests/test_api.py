from fastapi.testclient import TestClient

from app.main import app

# TestClient a nivel de módulo: NO dispara el lifespan, así que no intenta
# abrir el pool de base de datos. Estos tests no tocan la BD ni ORS.
client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_route_rechaza_altura_invalida():
    r = client.post("/api/route", json={
        "origin": {"lat": -33.0, "lon": -71.6},
        "destination": {"lat": -33.0, "lon": -71.5},
        "dimensions": {"height": 99, "width": 2.6, "length": 13, "weight": 30},
    })
    assert r.status_code == 422  # height > 6 m rechazado por Pydantic


def test_route_rechaza_coordenada_invalida():
    r = client.post("/api/route", json={
        "origin": {"lat": 999, "lon": -71.6},
        "destination": {"lat": -33.0, "lon": -71.5},
        "dimensions": {"height": 4.2, "width": 2.6, "length": 13, "weight": 30},
    })
    assert r.status_code == 422


def test_report_rechaza_tipo_faltante():
    r = client.post("/api/reports", json={"lat": -33.0, "lon": -71.6})
    assert r.status_code == 422
