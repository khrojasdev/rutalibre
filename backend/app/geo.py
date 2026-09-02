"""Utilidades geoespaciales puras (sin I/O): comparación de rutas y
construcción de polígonos de exclusión para openrouteservice.

Se mantienen sin dependencias externas para que sean fáciles de testear.
"""


def divergent_segments(
    car: list[list[float]], truck: list[list[float]], precision: int = 4
) -> list[list[list[float]]]:
    """Tramos de la ruta AUTO que la ruta CAMIÓN evitó.

    Heurística: se comparan coordenadas [lon, lat] redondeadas a `precision`
    decimales (~11 m a 4 decimales). Los puntos de la ruta de auto que no
    aparecen en la ruta de camión forman los tramos "evitados".

    Es una aproximación geométrica pensada para VISUALIZAR la divergencia,
    no una consulta a las etiquetas OSM. Esta limitación está documentada
    en el README (roadmap: Overpass API para explicar el porqué del desvío).
    """
    truck_set = {(round(x, precision), round(y, precision)) for x, y in truck}
    segments: list[list[list[float]]] = []
    current: list[list[float]] = []
    for x, y in car:
        if (round(x, precision), round(y, precision)) in truck_set:
            if len(current) > 1:
                segments.append(current)
            current = []
        else:
            current.append([x, y])
    if len(current) > 1:
        segments.append(current)
    return segments


def reports_to_avoid_polygons(
    points: list[tuple[float, float]], delta: float = 0.0004
) -> dict | None:
    """Convierte reportes verificados (lat, lon) en un MultiPolygon de
    cuadrados (~40 m de lado a `delta`=0.0004) que ORS acepta en
    options.avoid_polygons. Devuelve None si no hay reportes.

    Cada anillo se cierra repitiendo el primer vértice, como exige GeoJSON.
    El orden de coordenadas es [lon, lat].
    """
    if not points:
        return None
    polys: list[list[list[list[float]]]] = []
    for lat, lon in points:
        ring = [
            [lon - delta, lat - delta],
            [lon + delta, lat - delta],
            [lon + delta, lat + delta],
            [lon - delta, lat + delta],
            [lon - delta, lat - delta],  # cierre del anillo
        ]
        polys.append([ring])
    return {"type": "MultiPolygon", "coordinates": polys}
