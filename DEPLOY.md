# 🚀 DEPLOY de RutaLibre — paso a paso desde cero

Todo gratis, todo en línea. Sigue el orden. Tiempo estimado: ~40 min.
Lo que necesitas tener a mano al final: **la API key de ORS** y **el connection
string de Neon** (los obtienes en los pasos 1 y 2).

---

## Paso 1 · openrouteservice (motor de ruteo)

1. Entra a https://openrouteservice.org y crea una cuenta (Sign up).
2. Ve al **Dashboard** → pestaña **Tokens** → **Request a token** (plan gratuito).
3. Copia el token. Es tu `ORS_API_KEY`. Guárdalo en un lugar seguro (NO en el repo).

**Validación temprana** (reemplaza `TU_KEY`): ruta Valparaíso → Viña como camión de 4,2 m.

```bash
curl -s -X POST "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson" \
  -H "Authorization: TU_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [[-71.6197, -33.0458], [-71.5518, -33.0245]],
    "language": "es",
    "options": {"vehicle_type": "hgv",
      "profile_params": {"restrictions": {"height": 4.2, "width": 2.6, "length": 13.0, "weight": 30.0}}}
  }' | head -c 400
```

✅ Debe devolver un JSON con `"type":"FeatureCollection"`. Si da `403`, la key
está mal. **No sigas hasta que esto funcione.**

---

## Paso 2 · Neon (base de datos PostGIS)

1. Entra a https://neon.tech y crea una cuenta (puedes usar GitHub).
2. **Create project**: nombre `rutalibre`, región **AWS · US East (Ohio)**. Create.
3. En **Dashboard → Connection Details**, copia el **connection string**. Se ve así:
   `postgresql://usuario:PASSWORD@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require`
   Es tu `DATABASE_URL`. La parte sensible es el `PASSWORD` — no lo compartas.
4. Abre **SQL Editor** (menú lateral), pega TODO el contenido de `db/init.sql` y **Run**.
5. Verifica: en el mismo editor ejecuta

   ```sql
   SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;
   ```

   ✅ Deben aparecer: `reports`, `restricted_zones`, `routes`, `vehicles`.

> Para probar la capa colaborativa al final, descomenta el bloque SEED al pie de
> `db/init.sql` y ejecútalo: inserta un reporte verificado sobre la ruta de ejemplo.

---

## Paso 3 · Subir el código a GitHub

Desde la carpeta del proyecto:

```bash
git init
git add .
git commit -m "MVP RutaLibre: ORS + FastAPI + React/MapLibre + Neon PostGIS"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/rutalibre.git
git push -u origin main
```

> El `.gitignore` ya excluye `.env`, `node_modules/` y `dist/`. Verifica con
> `git status` que **no** aparezca ningún `.env` antes de hacer commit.

---

## Paso 4 · Backend en Render

**Opción A — con el blueprint (recomendada):**
1. https://render.com → inicia sesión con GitHub.
2. **New → Blueprint** → selecciona el repo `rutalibre`. Render detecta `render.yaml`.
3. Te pedirá las 3 variables marcadas: pega `ORS_API_KEY`, `DATABASE_URL` (la de
   Neon) y `ALLOWED_ORIGINS` (por ahora pon `http://localhost:5173`, la corriges
   en el paso 6). Apply.

**Opción B — manual:** New → Web Service → repo → Root Directory `backend`,
Build `pip install -r requirements.txt`, Start
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`, Instance **Free**, y agrega
las 3 variables de entorno.

Al terminar tendrás una URL tipo `https://rutalibre-api.onrender.com`.

✅ Verifica: `https://rutalibre-api.onrender.com/api/health` → `{"status":"ok"}`
(la primera carga puede tardar ~30–60 s porque el servicio despierta).

---

## Paso 5 · Frontend en Cloudflare Pages

1. https://dash.cloudflare.com → **Workers & Pages → Create → Pages → Connect to Git**.
2. Selecciona el repo `rutalibre`.
3. Configuración de build:
   - **Framework preset:** Vite
   - **Root directory:** `frontend`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
4. **Environment variables** (¡importante, Vite las inyecta al construir!):
   - `VITE_API_URL` = `https://rutalibre-api.onrender.com` (tu URL de Render)
5. **Save and Deploy.** Tendrás una URL tipo `https://rutalibre.pages.dev`.

> **Alternativa Vercel:** Add New → Project → repo → Root Directory `frontend`
> (detecta Vite solo) → env var `VITE_API_URL` = tu URL de Render → Deploy.

---

## Paso 6 · Conectar CORS (último ajuste)

El backend solo acepta peticiones de orígenes que conoce. Vuelve a **Render →
tu servicio → Environment** y cambia:

```
ALLOWED_ORIGINS = https://rutalibre.pages.dev
```

(usa tu URL real de Cloudflare/Vercel). Guarda; Render redeploya solo en ~1 min.

---

## Paso 7 · Prueba end-to-end

1. Abre `https://rutalibre.pages.dev` **desde tu teléfono** (no desde tu PC — así
   compruebas que vive en internet sin depender de tu máquina).
2. Toca dos puntos en el mapa (Valparaíso y Viña), ajusta el alto a 4,2 m,
   **Calcular ruta**. Verás la ruta camión azul, la de auto gris punteada y los
   tramos evitados en rojo.
3. Si ejecutaste el SEED del paso 2, el panel mostrará "1 reporte(s) de
   conductores aplicados" y la ruta esquivará ese punto.

---

## (Opcional) Paso 8 · Mantener despierto el backend

Render free duerme tras 15 min. Para que la demo cargue rápido cuando la revise
un reclutador:

1. https://cron-job.org → crea cuenta gratis.
2. Nuevo cronjob: URL `https://rutalibre-api.onrender.com/api/health`, cada 10 min.

O simplemente ponlo en el README ("el backend gratuito tarda unos segundos en
despertar") — es una limitación entendida y honesta.

---

## Checklist de deploy

- [ ] ORS: token creado y `curl` de prueba responde 200
- [ ] Neon: proyecto creado, `init.sql` ejecutado, 4 tablas verificadas
- [ ] GitHub: repo subido, sin `.env` en el historial
- [ ] Render: servicio vivo, `/api/health` responde
- [ ] Cloudflare Pages: build OK, `VITE_API_URL` apuntando a Render
- [ ] CORS: `ALLOWED_ORIGINS` con la URL real del frontend
- [ ] Prueba desde el teléfono: ruta camión vs auto se dibuja
- [ ] README: pegar la URL de la demo en vivo
