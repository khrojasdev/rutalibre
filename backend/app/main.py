"""RutaLibre API — FastAPI.

Endpoints:
  GET  /api/health   → estado
  POST /api/route    → ruta camión + ruta auto de comparación + tramos evitados
  POST /api/reports  → crear reporte colaborativo
  GET  /api/reports  → listar reportes
"""

import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # carga backend/.env antes de leer variables de entorno

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from .db import pool  # noqa: E402
from .geo import divergent_segments, reports_to_avoid_polygons  # noqa: E402
from .ors import get_route  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Abre el pool al arrancar (no al importar, para no romper los tests).
    if os.getenv("DATABASE_URL"):
        pool.open()
    yield
    if not pool.closed:
        pool.close()


app = FastAPI(title="RutaLibre API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Schemas ----------

class Point(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class Dimensions(BaseModel):
    height: float = Field(..., gt=0, le=6, description="metros")
    width: float = Field(..., gt=0, le=4, description="metros")
    length: float = Field(..., gt=0, le=30, description="metros")
    weight: float = Field(..., gt=0, le=100, description="toneladas")


class RouteRequest(BaseModel):
    origin: Point
    destination: Point
    dimensions: Dimensions


class ReportIn(BaseModel):
    type: str = Field(..., description="puente_bajo|calle_angosta|viraje_imposible|peso_restringido|otro")
    description: str | None = None
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


# ---------- Helpers ----------

def _to_feature(ors_feature: dict, kind: str) -> dict:
    props = ors_feature["properties"]
    maneuvers = [
        {"instruction": s["instruction"], "length_km": round(s["distance"] / 1000, 2)}
        for seg in props.get("segments", [])
        for s in seg.get("steps", [])
    ]
    return {
        "type": "Feature",
        "properties": {
            "kind": kind,
            "distance_km": round(props["summary"]["distance"] / 1000, 1),
            "duration_min": round(props["summary"]["duration"] / 60, 1),
            "maneuvers": maneuvers,
        },
        "geometry": ors_feature["geometry"],
    }


def _verified_reports(o: Point, d: Point) -> list[tuple[float, float]]:
    """Reportes 'verificado' dentro del bounding box origen-destino (con margen)."""
    with pool.connection() as conn:
        rows = conn.execute(
            """
            SELECT ST_Y(geom), ST_X(geom) FROM reports
            WHERE status = 'verificado'
              AND geom && ST_Expand(ST_MakeEnvelope(%s, %s, %s, %s, 4326), 0.02)
            LIMIT 40
            """,
            (min(o.lon, d.lon), min(o.lat, d.lat), max(o.lon, d.lon), max(o.lat, d.lat)),
        ).fetchall()
    return [(lat, lon) for lat, lon in rows]


# ---------- Endpoints ----------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/route")
async def route(req: RouteRequest):
    coords = [
        [req.origin.lon, req.origin.lat],
        [req.destination.lon, req.destination.lat],
    ]
    reports = _verified_reports(req.origin, req.destination)
    avoid = reports_to_avoid_polygons(reports)

    truck_raw, car_raw = await asyncio.gather(
        get_route("driving-hgv", coords, req.dimensions.model_dump(), avoid),
        get_route("driving-car", coords),
    )

    truck_f = _to_feature(truck_raw, "truck")
    car_f = _to_feature(car_raw, "car")
    avoided = divergent_segments(
        car_f["geometry"]["coordinates"], truck_f["geometry"]["coordinates"]
    )

    return {
        "truck": truck_f,
        "car": car_f,
        "avoided": {
            "type": "Feature",
            "properties": {"kind": "avoided"},
            "geometry": {"type": "MultiLineString", "coordinates": avoided},
        },
        "comparison": {
            "extra_km": round(
                truck_f["properties"]["distance_km"] - car_f["properties"]["distance_km"], 1
            ),
            "extra_min": round(
                truck_f["properties"]["duration_min"] - car_f["properties"]["duration_min"], 1
            ),
            "n_avoided_segments": len(avoided),
            "exclusions_applied": len(reports),
        },
    }


@app.post("/api/reports", status_code=201)
def create_report(r: ReportIn):
    with pool.connection() as conn:
        row = conn.execute(
            """INSERT INTO reports (type, description, geom)
               VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
               RETURNING id""",
            (r.type, r.description, r.lon, r.lat),
        ).fetchone()
    return {"id": row[0], "status": "pendiente"}


@app.get("/api/reports")
def list_reports():
    with pool.connection() as conn:
        rows = conn.execute(
            """SELECT id, type, description, status, votes,
                      ST_Y(geom) AS lat, ST_X(geom) AS lon
               FROM reports ORDER BY created_at DESC LIMIT 200"""
        ).fetchall()
    return [
        {"id": i, "type": t, "description": de, "status": s,
         "votes": v, "lat": la, "lon": lo}
        for i, t, de, s, v, la, lo in rows
    ]
