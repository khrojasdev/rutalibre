-- ============================================================
-- RutaLibre — esquema PostGIS
-- Ejecutar en Neon: proyecto → SQL Editor → pegar todo → Run
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- Perfiles de vehículo guardados ----------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    height_m    NUMERIC(4,2) NOT NULL CHECK (height_m > 0 AND height_m <= 6),
    width_m     NUMERIC(4,2) NOT NULL CHECK (width_m  > 0 AND width_m  <= 4),
    length_m    NUMERIC(5,2) NOT NULL CHECK (length_m > 0 AND length_m <= 30),
    weight_t    NUMERIC(5,2) NOT NULL CHECK (weight_t > 0 AND weight_t <= 100),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Historial de rutas calculadas -----------------------------------
CREATE TABLE IF NOT EXISTS routes (
    id           SERIAL PRIMARY KEY,
    vehicle_id   INTEGER REFERENCES vehicles(id) ON DELETE SET NULL,
    origin       geometry(Point, 4326) NOT NULL,
    destination  geometry(Point, 4326) NOT NULL,
    geom_truck   geometry(LineString, 4326),
    geom_car     geometry(LineString, 4326),
    distance_km  NUMERIC(7,2),
    duration_min NUMERIC(7,1),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Reportes colaborativos de conductores (modelo Waze) -------------
CREATE TABLE IF NOT EXISTS reports (
    id          SERIAL PRIMARY KEY,
    type        TEXT NOT NULL CHECK (type IN
                  ('puente_bajo','calle_angosta','viraje_imposible','peso_restringido','otro')),
    description TEXT,
    geom        geometry(Point, 4326) NOT NULL,
    photo_url   TEXT,
    status      TEXT NOT NULL DEFAULT 'pendiente'
                  CHECK (status IN ('pendiente','verificado','rechazado')),
    votes       INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Zonas con restricción horaria municipal (v3) --------------------
CREATE TABLE IF NOT EXISTS restricted_zones (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    geom       geometry(Polygon, 4326) NOT NULL,
    schedule   JSONB,   -- ej: {"dias":[1,2,3,4,5],"desde":"07:00","hasta":"21:00"}
    source     TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices espaciales ----------------------------------------------
CREATE INDEX IF NOT EXISTS idx_reports_geom          ON reports          USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_routes_origin         ON routes           USING GIST (origin);
CREATE INDEX IF NOT EXISTS idx_restricted_zones_geom ON restricted_zones USING GIST (geom);

-- ============================================================
-- SEED OPCIONAL — para probar la capa colaborativa end-to-end.
-- Punto sobre la ruta Valparaíso → Viña. Ejecutar SOLO si quieres
-- ver un reporte verificado desviando la ruta del camión.
-- ============================================================
-- INSERT INTO reports (type, description, geom, status)
-- VALUES ('puente_bajo', 'Paso bajo nivel 3,8 m no mapeado en OSM',
--         ST_SetSRID(ST_MakePoint(-71.59, -33.036), 4326), 'verificado');

-- ============================================================
-- Verificación (ejecutar después del Run principal):
--   SELECT PostGIS_Version();
--   SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- Deben aparecer: reports, restricted_zones, routes, vehicles
-- ============================================================
