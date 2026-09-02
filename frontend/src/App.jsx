import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import './App.css'

const API = import.meta.env.VITE_API_URL || '' // en Vercel/Cloudflare apunta a Render
const EMPTY = { type: 'FeatureCollection', features: [] }
const DEFAULT_DIMS = { height: 4.2, width: 2.6, length: 13, weight: 30 }

const DIM_FIELDS = [
  { key: 'height', label: 'Alto', unit: 'm', max: 6 },
  { key: 'width', label: 'Ancho', unit: 'm', max: 4 },
  { key: 'length', label: 'Largo', unit: 'm', max: 30 },
  { key: 'weight', label: 'Peso', unit: 't', max: 100 },
]

export default function App() {
  const mapRef = useRef(null)
  const mapDiv = useRef(null)
  const markers = useRef([])
  const [origin, setOrigin] = useState(null)
  const [destination, setDestination] = useState(null)
  const [dims, setDims] = useState(DEFAULT_DIMS)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Inicializar mapa
  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapDiv.current,
      style: 'https://tiles.openfreemap.org/styles/liberty',
      center: [-71.61, -33.045],
      zoom: 12,
      attributionControl: { compact: true },
    })
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    map.on('load', () => {
      map.addSource('car', { type: 'geojson', data: EMPTY })
      map.addSource('truck', { type: 'geojson', data: EMPTY })
      map.addSource('avoided', { type: 'geojson', data: EMPTY })
      map.addLayer({
        id: 'car', type: 'line', source: 'car',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#7a8794', 'line-width': 4, 'line-dasharray': [1.5, 1.8] },
      })
      map.addLayer({
        id: 'avoided', type: 'line', source: 'avoided',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#e5484d', 'line-width': 7, 'line-opacity': 0.85 },
      })
      map.addLayer({
        id: 'truck', type: 'line', source: 'truck',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#2f6fed', 'line-width': 5 },
      })
    })

    mapRef.current = map
    return () => map.remove()
  }, [])

  // Clic 1 = origen, clic 2 = destino, clic 3 = reiniciar
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const onClick = (e) => {
      const p = { lat: e.lngLat.lat, lon: e.lngLat.lng }
      if (!origin) setOrigin(p)
      else if (!destination) setDestination(p)
      else {
        setOrigin(p); setDestination(null); setResult(null)
        for (const s of ['car', 'truck', 'avoided']) map.getSource(s)?.setData(EMPTY)
      }
    }
    map.on('click', onClick)
    return () => map.off('click', onClick)
  }, [origin, destination])

  // Marcadores de origen / destino
  useEffect(() => {
    markers.current.forEach((m) => m.remove())
    markers.current = []
    const map = mapRef.current
    if (!map) return
    for (const [p, cls] of [[origin, 'origin'], [destination, 'dest']]) {
      if (!p) continue
      const el = document.createElement('div')
      el.className = `pin pin--${cls}`
      markers.current.push(
        new maplibregl.Marker({ element: el, anchor: 'bottom' })
          .setLngLat([p.lon, p.lat]).addTo(map)
      )
    }
  }, [origin, destination])

  async function calculate() {
    setLoading(true); setError(null)
    try {
      const r = await fetch(`${API}/api/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin, destination,
          dimensions: {
            height: +dims.height, width: +dims.width,
            length: +dims.length, weight: +dims.weight,
          },
        }),
      })
      if (!r.ok) {
        const body = await r.json().catch(() => ({}))
        throw new Error(body.detail || 'No se pudo calcular la ruta.')
      }
      const data = await r.json()
      setResult(data)
      const map = mapRef.current
      map.getSource('car').setData(data.car)
      map.getSource('truck').setData(data.truck)
      map.getSource('avoided').setData(data.avoided)
      const coords = data.truck.geometry.coordinates
      const bounds = coords.reduce(
        (b, c) => b.extend(c),
        new maplibregl.LngLatBounds(coords[0], coords[0])
      )
      map.fitBounds(bounds, { padding: 70, duration: 600 })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setOrigin(null); setDestination(null); setResult(null); setError(null)
    const map = mapRef.current
    for (const s of ['car', 'truck', 'avoided']) map?.getSource(s)?.setData(EMPTY)
  }

  const step = !origin ? 'Marca el origen en el mapa'
    : !destination ? 'Marca el destino en el mapa'
    : 'Listo para calcular'

  return (
    <div className="app">
      <aside className="panel">
        <header className="brand">
          <span className="brand__mark" aria-hidden="true">▟</span>
          <div>
            <h1 className="brand__name">RutaLibre</h1>
            <p className="brand__tag">Rutas según el tamaño real de tu vehículo</p>
          </div>
        </header>

        <ol className="waypoints">
          <li className={origin ? 'is-set' : ''}>
            <span className="waypoints__dot waypoints__dot--origin" />
            <span>{origin ? `${origin.lat.toFixed(4)}, ${origin.lon.toFixed(4)}` : 'Origen'}</span>
          </li>
          <li className={destination ? 'is-set' : ''}>
            <span className="waypoints__dot waypoints__dot--dest" />
            <span>{destination ? `${destination.lat.toFixed(4)}, ${destination.lon.toFixed(4)}` : 'Destino'}</span>
          </li>
        </ol>
        <p className="step">{step}</p>

        <div className="gauges">
          {DIM_FIELDS.map(({ key, label, unit, max }) => (
            <label key={key} className="gauge">
              <span className="gauge__label">{label}</span>
              <span className="gauge__field">
                <input
                  type="number" step="0.1" min="0" max={max}
                  value={dims[key]}
                  onChange={(e) => setDims({ ...dims, [key]: e.target.value })}
                />
                <span className="gauge__unit">{unit}</span>
              </span>
            </label>
          ))}
        </div>

        <div className="actions">
          <button className="btn btn--primary" onClick={calculate}
            disabled={!origin || !destination || loading}>
            {loading ? 'Calculando…' : 'Calcular ruta'}
          </button>
          <button className="btn btn--ghost" onClick={reset} disabled={loading}>
            Reiniciar
          </button>
        </div>

        {error && <p className="alert">{error}</p>}

        {result && (
          <div className="readout">
            <div className="readout__rows">
              <div className="readout__row">
                <span className="tag tag--truck">Camión</span>
                <span>{result.truck.properties.distance_km} km</span>
                <span>{result.truck.properties.duration_min} min</span>
              </div>
              <div className="readout__row">
                <span className="tag tag--car">Auto</span>
                <span>{result.car.properties.distance_km} km</span>
                <span>{result.car.properties.duration_min} min</span>
              </div>
            </div>

            <div className="cost">
              <span className="cost__label">Costo de ir grande</span>
              <span className="cost__value">
                +{result.comparison.extra_km} km · +{result.comparison.extra_min} min
              </span>
            </div>

            <p className="readout__note">
              <span className="tag tag--avoided">Evitó</span>
              {result.comparison.n_avoided_segments} tramo(s) intransitables para tus dimensiones.
            </p>

            {result.comparison.exclusions_applied > 0 && (
              <p className="readout__reports">
                {result.comparison.exclusions_applied} reporte(s) de conductores aplicados a esta ruta.
              </p>
            )}
          </div>
        )}
      </aside>

      <div ref={mapDiv} className="map" />
    </div>
  )
}
