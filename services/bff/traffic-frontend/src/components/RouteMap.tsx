import { useRef, useEffect, useCallback, type RefObject } from "react"
import { Map, Marker, GeoJSONSource, NavigationControl, MapMouseEvent, LngLatBounds } from "mapbox-gl"
import mapboxgl from 'mapbox-gl'

type SegmentData = {
  segment_id: string
  coordinates: unknown
  capacity: number | null
  utilization?: number
}

type Coord = { lng: number; lat: number }

type Props = {
  geometry?: GeoJSON.Geometry | null
  segments?: SegmentData[]
  origin?: Coord | null
  destination?: Coord | null
  onMapClick?: (lngLat: Coord) => void
}

const DUBLIN_CENTER: [number, number] = [-6.26, 53.35]

function utilizationColor(ratio: number): string {
  const clamped = Math.min(Math.max(ratio, 0), 1)
  const green = { r: 0x22, g: 0xc5, b: 0x5e }
  const yellow = { r: 0xea, g: 0xb3, b: 0x08 }
  const red = { r: 0xef, g: 0x44, b: 0x44 }

  let r: number, g: number, b: number
  if (clamped <= 0.5) {
    const t = clamped / 0.5
    r = Math.round(green.r + (yellow.r - green.r) * t)
    g = Math.round(green.g + (yellow.g - green.g) * t)
    b = Math.round(green.b + (yellow.b - green.b) * t)
  } else {
    const t = (clamped - 0.5) / 0.5
    r = Math.round(yellow.r + (red.r - yellow.r) * t)
    g = Math.round(yellow.g + (red.g - yellow.g) * t)
    b = Math.round(yellow.b + (red.b - yellow.b) * t)
  }

  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`
}

function RouteMap({ geometry, segments, origin, destination, onMapClick }: Props) {
  const mapRef = useRef<Map | null>(null)
  const markersRef = useRef<Marker[]>([])
  const onMapClickRef = useRef(onMapClick)

  useEffect(() => {
    onMapClickRef.current = onMapClick
  }, [onMapClick])

  const containerRef = useCallback((node: HTMLDivElement | null) => {
    if (mapRef.current) {
      mapRef.current.remove()
      mapRef.current = null
    }
    if (!node) return

    const token = import.meta.env.VITE_MAPBOX_TOKEN
    if (!token) {
      console.warn("MAPBOX_TOKEN not set — map will not render")
      return
    }

    mapboxgl.accessToken = token

    const map = new Map({
      container: node,
      style: "mapbox://styles/mapbox/streets-v12",
      center: DUBLIN_CENTER,
      zoom: 11,
    })

    map.addControl(new NavigationControl(), "top-right")

    map.on("click", (e: MapMouseEvent) => {
      onMapClickRef.current?.({ lng: e.lngLat.lng, lat: e.lngLat.lat })
    })

    mapRef.current = map
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    function sync() {
      syncRouteLine(map!, geometry)
      syncSegmentLayers(map!, segments)
      syncMarkers(map!, markersRef, origin, destination)
      fitBoundsToGeometry(map!, geometry)
    }

    if (map.loaded()) {
      sync()
    } else {
      map.once("idle", sync)
      return () => {
        map.off("idle", sync)
      }
    }
  }, [geometry, segments, origin, destination])

  return (
    <div
      ref={containerRef}
      className="h-[400px] w-full rounded-lg border"
      style={{ minHeight: 400 }}
    />
  )
}

function syncRouteLine(map: Map, geometry: GeoJSON.Geometry | null | undefined) {
  const sourceId = "route-line"
  const layerId = "route-line-layer"

  if (!geometry) {
    if (map.getLayer(layerId)) map.removeLayer(layerId)
    if (map.getSource(sourceId)) map.removeSource(sourceId)
    return
  }

  const geojson: GeoJSON.Feature = {
    type: "Feature",
    properties: {},
    geometry,
  }

  if (map.getSource(sourceId)) {
    ; (map.getSource(sourceId) as GeoJSONSource).setData(geojson)
  } else {
    map.addSource(sourceId, { type: "geojson", data: geojson })
    map.addLayer({
      id: layerId,
      type: "line",
      source: sourceId,
      paint: {
        "line-color": "#3b82f6",
        "line-width": 4,
        "line-opacity": 0.8,
      },
    })
  }
}

function syncSegmentLayers(map: Map, segments: SegmentData[] | undefined) {
  const style = map.getStyle()
  if (style?.layers) {
    for (const layer of style.layers) {
      if (layer.id.startsWith("segment-")) {
        map.removeLayer(layer.id)
      }
    }
  }
  if (style?.sources) {
    for (const sourceId of Object.keys(style.sources)) {
      if (sourceId.startsWith("segment-")) {
        map.removeSource(sourceId)
      }
    }
  }

  if (!segments || segments.length === 0) {
    return
  }

  for (const seg of segments) {
    if (!seg.coordinates) continue

    const sourceId = `segment-${seg.segment_id}`
    const layerId = `segment-${seg.segment_id}-layer`
    const color = utilizationColor(seg.utilization ?? 0)

    const geojson: GeoJSON.Feature = {
      type: "Feature",
      properties: {},
      geometry: toLineGeometry(seg.coordinates),
    }

    map.addSource(sourceId, { type: "geojson", data: geojson })
    map.addLayer({
      id: layerId,
      type: "line",
      source: sourceId,
      paint: {
        "line-color": color,
        "line-width": 6,
        "line-opacity": 0.7,
      },
    })
  }
}

function syncMarkers(
  map: Map,
  markersRef: RefObject<Marker[]>,
  origin: Coord | null | undefined,
  destination: Coord | null | undefined,
) {
  for (const m of markersRef.current) m.remove()
  markersRef.current = []

  if (origin) {
    const m = new Marker({ color: "#22c55e" })
      .setLngLat([origin.lng, origin.lat])
      .addTo(map)
    markersRef.current.push(m)
  }
  if (destination) {
    const m = new Marker({ color: "#ef4444" })
      .setLngLat([destination.lng, destination.lat])
      .addTo(map)
    markersRef.current.push(m)
  }
}

function fitBoundsToGeometry(map: Map, geometry: GeoJSON.Geometry | null | undefined) {
  if (!geometry) return
  try {
    const coords = extractCoordinates(geometry)
    if (coords.length > 0) {
      const bounds = coords.reduce(
        (b, coord) => b.extend(coord as [number, number]),
        new LngLatBounds(coords[0] as [number, number], coords[0] as [number, number]),
      )
      map.fitBounds(bounds, { padding: 60 })
    }
  } catch (err) {
    console.error(err)
  }
}


function extractCoordinates(geometry: unknown): number[][] {
  const geo = geometry as { type: string; coordinates: unknown }
  if (!geo?.type || !geo?.coordinates) return []
  if (geo.type === "LineString") return geo.coordinates as number[][]
  if (geo.type === "MultiLineString") return (geo.coordinates as number[][][]).flat()
  if (geo.type === "Point") return [geo.coordinates as number[]]
  return []
}

function toLineGeometry(coordinates: unknown): GeoJSON.Geometry {
  if (
    Array.isArray(coordinates) &&
    coordinates.length > 0 &&
    Array.isArray(coordinates[0]) &&
    Array.isArray(coordinates[0][0])
  ) {
    return { type: "MultiLineString", coordinates: coordinates as number[][][] }
  }
  return { type: "LineString", coordinates: coordinates as number[][] }
}

export default RouteMap
