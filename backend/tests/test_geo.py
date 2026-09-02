from app.geo import divergent_segments, reports_to_avoid_polygons


def test_divergent_segments_detecta_tramo_evitado():
    truck = [[0.0, 0.0], [0.001, 0.0], [0.002, 0.0]]
    car = [[0.0, 0.0], [0.5, 0.5], [0.6, 0.5], [0.002, 0.0]]
    segs = divergent_segments(car, truck)
    assert len(segs) == 1
    assert segs[0] == [[0.5, 0.5], [0.6, 0.5]]


def test_rutas_identicas_sin_divergencia():
    r = [[0.0, 0.0], [0.001, 0.001]]
    assert divergent_segments(r, r) == []


def test_divergencia_ignora_punto_aislado():
    # Un solo punto divergente no forma segmento (necesita >1 punto).
    truck = [[0.0, 0.0], [0.002, 0.0]]
    car = [[0.0, 0.0], [0.5, 0.5], [0.002, 0.0]]
    assert divergent_segments(car, truck) == []


def test_avoid_polygons_vacio_devuelve_none():
    assert reports_to_avoid_polygons([]) is None


def test_avoid_polygons_genera_multipolygon_cerrado():
    mp = reports_to_avoid_polygons([(-33.0, -71.6)])
    assert mp["type"] == "MultiPolygon"
    ring = mp["coordinates"][0][0]
    assert len(ring) == 5           # 4 vértices + cierre
    assert ring[0] == ring[-1]      # anillo cerrado


def test_avoid_polygons_multiples_puntos():
    mp = reports_to_avoid_polygons([(-33.0, -71.6), (-33.1, -71.5)])
    assert len(mp["coordinates"]) == 2
