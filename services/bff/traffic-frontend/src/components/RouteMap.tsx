import { useRef, useEffect, useCallback, type RefObject } from "react"
import { Map, Marker, GeoJSONSource, NavigationControl, MapMouseEvent, LngLatBounds } from "mapbox-gl"
import mapboxgl from 'mapbox-gl'
import { cn } from "@/lib/utils"

type SegmentData = {
  segment_id: string
  name?: string
  region?: string
  coordinates: unknown
  capacity: number | null
  reserved?: number
  utilization?: number
}

type Coord = { lng: number; lat: number }

type Props = {
  geometry?: GeoJSON.Geometry | null
  segments?: SegmentData[]
  origin?: Coord | null
  destination?: Coord | null
  onMapClick?: (lngLat: Coord) => void
  className?: string
}

const DUBLIN_CENTER: [number, number] = [-6.26, 53.35]
const SEGMENT_OUTLINE_LAYER_ID = "route-segment-outline"
const SEGMENT_LAYER_ID = "route-segment-lines"
const SEGMENT_HITBOX_LAYER_ID = "route-segment-hitbox"
const SEGMENT_SOURCE_ID = "route-segments"
const SEGMENT_BOUNDARY_LAYER_ID = "route-segment-boundaries"
const SEGMENT_BOUNDARY_SOURCE_ID = "route-segment-boundaries"
const SEGMENT_AVAILABLE_COLOR = "#86efac"
const SEGMENT_MEDIUM_COLOR = "#fde68a"
const SEGMENT_FULL_COLOR = "#fca5a5"

function segmentCapacityColor(reserved: number, capacity: number): string {
  if (capacity <= 0) return SEGMENT_AVAILABLE_COLOR
  if (reserved >= capacity) return SEGMENT_FULL_COLOR
  if (reserved / capacity >= 0.5) return SEGMENT_MEDIUM_COLOR
  return SEGMENT_AVAILABLE_COLOR
}

function RouteMap({ geometry, segments, origin, destination, onMapClick, className }: Props) {
  const mapRef = useRef<Map | null>(null)
  const markersRef = useRef<Marker[]>([])
  const popupRef = useRef<mapboxgl.Popup | null>(null)
  const onMapClickRef = useRef(onMapClick)

  useEffect(() => {
    onMapClickRef.current = onMapClick
  }, [onMapClick])

  const containerRef = useCallback((node: HTMLDivElement | null) => {
    if (mapRef.current) {
      popupRef.current?.remove()
      mapRef.current.remove()
      mapRef.current = null
      popupRef.current = null
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

    const popup = new mapboxgl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
    })
    popupRef.current = popup

    map.on("click", (e: MapMouseEvent) => {
      onMapClickRef.current?.({ lng: e.lngLat.lng, lat: e.lngLat.lat })
    })

    map.on("mousemove", (e: MapMouseEvent) => {
      if (!map.getLayer(SEGMENT_HITBOX_LAYER_ID)) {
        map.getCanvas().style.cursor = ""
        popup.remove()
        return
      }
      const features = map.queryRenderedFeatures(e.point, { layers: [SEGMENT_HITBOX_LAYER_ID] })
      const feature = features[0]

      if (!feature) {
        map.getCanvas().style.cursor = ""
        popup.remove()
        return
      }

      map.getCanvas().style.cursor = "pointer"
      popup
        .setLngLat(e.lngLat)
        .setHTML(segmentPopupHtml(feature.properties ?? {}))
        .addTo(map)
    })

    map.on("mouseleave", () => {
      map.getCanvas().style.cursor = ""
      popup.remove()
    })

    mapRef.current = map
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    function sync() {
      syncRouteLine(map!, segments?.length ? null : geometry)
      syncSegmentLayers(map!, segments, geometry)
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
      className={cn("h-[400px] w-full rounded-lg border", className)}
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

function syncSegmentLayers(
  map: Map,
  segments: SegmentData[] | undefined,
  routeGeometry: GeoJSON.Geometry | null | undefined,
) {
  if (!segments || segments.length === 0) {
    if (map.getLayer(SEGMENT_BOUNDARY_LAYER_ID)) map.removeLayer(SEGMENT_BOUNDARY_LAYER_ID)
    if (map.getLayer(SEGMENT_HITBOX_LAYER_ID)) map.removeLayer(SEGMENT_HITBOX_LAYER_ID)
    if (map.getLayer(SEGMENT_LAYER_ID)) map.removeLayer(SEGMENT_LAYER_ID)
    if (map.getLayer(SEGMENT_OUTLINE_LAYER_ID)) map.removeLayer(SEGMENT_OUTLINE_LAYER_ID)
    if (map.getSource(SEGMENT_BOUNDARY_SOURCE_ID)) map.removeSource(SEGMENT_BOUNDARY_SOURCE_ID)
    if (map.getSource(SEGMENT_SOURCE_ID)) map.removeSource(SEGMENT_SOURCE_ID)
    return
  }

  const fallbackGeometries = splitRouteIntoSegmentGeometries(routeGeometry, segments.length)
  const features = segments.flatMap((seg, index) => {
    const segmentGeometry = normalizeLineGeometry(seg.coordinates) ?? fallbackGeometries[index]
    if (!segmentGeometry) return []

    const capacity = seg.capacity ?? 0
    const reserved = seg.reserved ?? Math.round((seg.utilization ?? 0) * capacity)
    const geojson: GeoJSON.Feature = {
      type: "Feature",
      properties: {
        color: segmentCapacityColor(reserved, capacity),
        capacity,
        reserved,
        segmentId: seg.segment_id,
        name: seg.name || "unnamed",
        region: seg.region || "Unknown",
        utilizationPercent: Math.round((seg.utilization ?? 0) * 100),
      },
      geometry: segmentGeometry,
    }
    return [geojson]
  })

  const geojson: GeoJSON.FeatureCollection = {
    type: "FeatureCollection",
    features,
  }
  const boundaryGeojson = segmentBoundaryGeojson(features)

  if (map.getSource(SEGMENT_SOURCE_ID)) {
    ; (map.getSource(SEGMENT_SOURCE_ID) as GeoJSONSource).setData(geojson)
    ; (map.getSource(SEGMENT_BOUNDARY_SOURCE_ID) as GeoJSONSource | undefined)?.setData(boundaryGeojson)
  } else {
    map.addSource(SEGMENT_SOURCE_ID, { type: "geojson", data: geojson })
    map.addSource(SEGMENT_BOUNDARY_SOURCE_ID, { type: "geojson", data: boundaryGeojson })
    map.addLayer({
      id: SEGMENT_OUTLINE_LAYER_ID,
      type: "line",
      source: SEGMENT_SOURCE_ID,
      layout: {
        "line-cap": "round",
        "line-join": "round",
      },
      paint: {
        "line-color": "#ffffff",
        "line-width": 11,
        "line-opacity": 0.85,
      },
    })
    map.addLayer({
      id: SEGMENT_LAYER_ID,
      type: "line",
      source: SEGMENT_SOURCE_ID,
      layout: {
        "line-cap": "round",
        "line-join": "round",
      },
      paint: {
        "line-color": ["get", "color"],
        "line-width": 7,
        "line-opacity": 0.9,
      },
    })
    map.addLayer({
      id: SEGMENT_HITBOX_LAYER_ID,
      type: "line",
      source: SEGMENT_SOURCE_ID,
      paint: {
        "line-color": "#000000",
        "line-width": 18,
        "line-opacity": 0,
      },
    })
    map.addLayer({
      id: SEGMENT_BOUNDARY_LAYER_ID,
      type: "circle",
      source: SEGMENT_BOUNDARY_SOURCE_ID,
      paint: {
        "circle-radius": 3,
        "circle-color": "#111827",
        "circle-opacity": 0.8,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 1.5,
      },
    })
  }
}

function segmentBoundaryGeojson(features: GeoJSON.Feature[]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: features.slice(0, -1).flatMap((feature) => {
      const coordinates = segmentEndCoordinate(feature.geometry)
      if (!coordinates) return []

      return [{
        type: "Feature",
        properties: {},
        geometry: {
          type: "Point",
          coordinates,
        },
      } satisfies GeoJSON.Feature<GeoJSON.Point>]
    }),
  }
}

function segmentEndCoordinate(geometry: GeoJSON.Geometry | null): [number, number] | null {
  if (!geometry) return null
  if (geometry.type === "LineString") {
    return toCoordinatePair(geometry.coordinates.at(-1))
  }
  if (geometry.type === "MultiLineString") {
    const lastLine = geometry.coordinates.findLast((line) => line.length > 0)
    return toCoordinatePair(lastLine?.at(-1))
  }
  return null
}

function toCoordinatePair(value: unknown): [number, number] | null {
  if (
    Array.isArray(value) &&
    typeof value[0] === "number" &&
    typeof value[1] === "number"
  ) {
    return [value[0], value[1]]
  }
  return null
}

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
}

function segmentPopupHtml(properties: GeoJSON.GeoJsonProperties): string {
  const name = escapeHtml(properties?.name || "unnamed")
  const region = escapeHtml(properties?.region || "Unknown")
  const capacity = Number(properties?.capacity ?? 0)
  const reserved = Number(properties?.reserved ?? 0)
  const utilizationPercent = Number(properties?.utilizationPercent ?? 0)

  return `
    <div style="min-width: 180px">
      <div style="font-weight: 700; margin-bottom: 4px">${name}</div>
      <div>Region: ${region}</div>
      <div>Capacity: ${capacity}</div>
      <div>Reserved: ${reserved} / ${capacity}</div>
      <div>Utilization: ${utilizationPercent}%</div>
    </div>
  `
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

function normalizeLineGeometry(value: unknown): GeoJSON.Geometry | null {
  const geo = value as { type?: string; coordinates?: unknown } | null | undefined
  if (geo?.type === "LineString" || geo?.type === "MultiLineString") {
    return geo as GeoJSON.Geometry
  }

  if (!Array.isArray(value)) return null
  return toLineGeometry(value)
}

function splitRouteIntoSegmentGeometries(
  routeGeometry: GeoJSON.Geometry | null | undefined,
  segmentCount: number,
): GeoJSON.Geometry[] {
  const coords = extractCoordinates(routeGeometry)
  if (segmentCount <= 0 || coords.length < 2) return []

  const edgeCount = coords.length - 1
  return Array.from({ length: segmentCount }, (_, index) => {
    const startIndex = Math.floor((index * edgeCount) / segmentCount)
    let endIndex = Math.floor(((index + 1) * edgeCount) / segmentCount)

    if (index === segmentCount - 1) endIndex = edgeCount
    if (endIndex <= startIndex) endIndex = Math.min(startIndex + 1, edgeCount)

    return {
      type: "LineString",
      coordinates: coords.slice(startIndex, endIndex + 1),
    } satisfies GeoJSON.LineString
  })
}

function toLineGeometry(coordinates: unknown[]): GeoJSON.Geometry {
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
