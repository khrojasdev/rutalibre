"""Cliente del motor de ruteo openrouteservice (API pública, capa gratuita).

Endpoint: /v2/directions/{profile}/geojson
- profile "driving-hgv" con vehicle_type=hgv y restricciones de dimensiones
- profile "driving-car" para la ruta de comparación

ORS usa orden de coordenadas [lon, lat]. La API key va en la variable de
entorno ORS_API_KEY, nunca en el código.
"""

import os

import httpx
from fastapi import HTTPException

ORS_URL = "https://api.openrouteservice.org/v2/directions"


async def get_route(
    profile: str,
    coordinates: list[list[float]],       # [[lon, lat], [lon, lat]]
    restrictions: dict | None = None,     # {height, width, length, weight}
    avoid_polygons: dict | None = None,   # GeoJSON MultiPolygon
) -> dict:
    """Llama a ORS y devuelve el primer Feature GeoJSON de la ruta.

    Lanza HTTPException(422) con el mensaje de ORS si el ruteo falla
    (p. ej. sin ruta posible para las dimensiones dadas).
    """
    body: dict = {"coordinates": coordinates, "instructions": True, "language": "es"}
    options: dict = {}
    if restrictions:
        options["vehicle_type"] = "hgv"
        options["profile_params"] = {"restrictions": restrictions}
    if avoid_polygons:
        options["avoid_polygons"] = avoid_polygons
    if options:
        body["options"] = options

    api_key = os.getenv("ORS_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="ORS_API_KEY no configurada")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{ORS_URL}/{profile}/geojson",
            json=body,
            headers={"Authorization": api_key, "Content-Type": "application/json"},
        )

    if r.status_code != 200:
        try:
            detail = r.json()["error"]["message"]
        except Exception:
            detail = r.text[:200]
        raise HTTPException(status_code=422, detail=f"ORS ({profile}): {detail}")

    features = r.json().get("features", [])
    if not features:
        raise HTTPException(status_code=422, detail=f"ORS ({profile}): sin ruta")
    return features[0]
