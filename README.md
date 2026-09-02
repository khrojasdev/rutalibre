# 🚛 RutaLibre

**Navegador web para camiones y buses en Chile.** El conductor ingresa las
dimensiones de su vehículo (alto, ancho, largo, peso) y obtiene rutas realmente
transitables, evitando puentes bajos, calles angostas y virajes imposibles —
con una ruta de auto de comparación que muestra visualmente qué evitó el camión.

**Demo en vivo:** _(pega aquí tu URL de Cloudflare Pages / Vercel tras el deploy)_

---

## El problema

Google Maps y Waze rutean para autos. Un camión de 4,2 m de alto o un bus de
13 m que sigue esas rutas termina atascado bajo un puente o en una calle
angosta: multas, daños y tacos. Los GPS de camión comerciales son caros y su
cobertura de datos en Chile es débil.

## La solución

RutaLibre usa el motor **openrouteservice** (perfil `driving-hgv`), que acepta
las dimensiones del vehículo por request y respeta las restricciones físicas
mapeadas en OpenStreetMap (`maxheight`, `maxwidth`, `maxweight`, `hgv`,
restricciones de viraje). Devuelve dos rutas superpuestas —camión y auto— y
resalta los tramos que el camión tuvo que evitar.

## Arquitectura

```
React + MapLibre GL           FastAPI                 openrouteservice
 (Cloudflare Pages)   ──▶   (Render, free)   ──▶   (perfil driving-hgv, datos OSM)
                                  │
                                  ▼
                         PostGIS en Neon
                (reportes colaborativos → avoid_polygons)
```

- **Frontend:** React (Vite) + MapLibre GL, tiles gratuitos de OpenFreeMap (sin API key).
- **Backend:** FastAPI + httpx + psycopg3, llamadas a ORS en paralelo (camión y auto).
- **Base de datos:** Postgres + PostGIS en Neon (serverless, free tier).
- **Motor de ruteo:** API pública de openrouteservice (free tier).

## El diferenciador: capa colaborativa (modelo Waze)

Los conductores reportan restricciones no mapeadas (puente bajo, calle
intransitable) con ubicación. Los reportes marcados como `verificado` que caen
dentro del área de la ruta se transforman en pequeños polígonos y se inyectan a
ORS como `avoid_polygons`, desviando la ruta. **La app mejora sus propios datos.**

## Decisiones técnicas (para entrevistas)

- **openrouteservice y no Google/Waze:** ORS expone las dimensiones del vehículo
  y las restricciones OSM por request, sin costo y sin reconstruir el grafo.
- **Ruta comparativa camión vs auto:** hace visible el valor del producto de un
  vistazo ("el costo de ir grande": +X km, +Y min).
- **Reportes → `avoid_polygons`:** convierte datos de la comunidad en decisiones
  de ruteo reales, no en simple decoración de mapa.
- **Infraestructura $0 y siempre en línea:** Cloudflare Pages + Render + Neon,
  sin servidores propios ni Docker que ejecutar localmente.

## Limitaciones conocidas (honestidad de ingeniería)

- El **ancho exacto de calle** rara vez está en OSM; el motor lo aproxima por
  número de pistas y categoría de vía.
- La detección de **"tramos evitados"** es una heurística geométrica de
  comparación de coordenadas entre ambas rutas, **no** una consulta a las
  etiquetas OSM. _(Roadmap: Overpass API para explicar el porqué de cada desvío
  con la etiqueta real.)_
- La **API pública de ORS** tiene límite de requests diarias (suficiente para
  desarrollo y demo).
- El **backend en Render free** se duerme tras ~15 min de inactividad; el primer
  request tarda ~30–60 s en despertar. Mitigación opcional: un ping cada 10 min
  a `/api/health` desde cron-job.org.
- **Valhalla self-hosted** (motor propio con OSM Chile) se evaluó y se descartó
  para el MVP por costo de infraestructura y RAM. Queda como ítem de roadmap: es
  el siguiente paso para eliminar los límites de la API pública.

## Correr en local

```bash
# 1. Base de datos: ejecutar db/init.sql en el SQL Editor de Neon.

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # completar ORS_API_KEY y DATABASE_URL
uvicorn app.main:app --reload
# → http://localhost:8000  (docs en /docs)

# 3. Frontend (otra terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Tests

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -v
```

## Deploy

Ver `DEPLOY.md` para el paso a paso completo (Neon → Render → Cloudflare Pages).

## Roadmap

- **v2:** verificación de reportes con votos + subida de fotos (Cloudinary).
- **v3:** zonas de restricción horaria municipal, modo flota, hoja de ruta en PDF.
- **Infra:** migrar a motor Valhalla self-hosted para eliminar límites de la API pública.
